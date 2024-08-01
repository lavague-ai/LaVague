import os
from typing import List, Tuple
import yaml
import time
from yaspin import yaspin
from yaspin.spinners import Spinners
from gherkin.parser import Parser
from selenium.webdriver.chrome.webdriver import WebDriver

from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.legacy.readers.file.base import SimpleDirectoryReader
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.context import Context
from lavague.core.token_counter import TokenCounter
from lavague.core.retrievers import SemanticRetriever
from lavague.drivers.selenium import SeleniumDriver
from lavague.qa.utils import (
    remove_comments,
    clean_llm_output,
    build_run_summary,
    to_snake_case,
    get_nav_action_code,
    get_nav_control_code,
    INDENT,
    INDENT_PASS,
)
from lavague.qa.prompts import FULL_PROMPT_TEMPLATE, ASSERT_ONLY_PROMPT_TEMPLATE


class Scenario:
    def __init__(self, name: str):
        self.name = name
        self.context: List[str] = []
        self.steps: List[str] = []
        self.expect: List[str] = []

    def __str__(self) -> str:
        return f"Context: {self.context}\nSteps: {self.steps}\nExpect: {self.expect}"

    def __repr__(self) -> str:
        return f"Scenario({str(self)})"


class TestGenerator:
    def __init__(
        self,
        context: Context, 
        url: str,
        feature_file_path: str,
        full_llm: bool,
        token_counter: TokenCounter,
        headless: bool,
        log_to_db: bool,
    ):
        self.context = context
        self.url = url
        self.feature_file_path = feature_file_path
        self.full_llm = full_llm
        self.token_counter = token_counter
        self.headless = headless
        self.log_to_db = log_to_db
        
        print(context)
        # parse feature
        self.scenarios, self.feature_file_content = self._read_scenarios(
            feature_file_path
        )
        self.scenario = self.scenarios[0]

        # setup target directory and file paths
        self.generated_dir = "./generated_tests"
        self._setup_file_paths()

        # instantiate LLMs
        # self.mm_llm = OpenAIMultiModal("gpt-4-vision-preview", max_new_tokens=1000)
        # self.llm = OpenAI(model="gpt-4")
        # self.embedding = OpenAIEmbedding(model="text-embedding-3-small")
        
        # instantiate LLMs for Pytest generation from context
        self.llm = self.context.llm
        self.mm_llm = self.context.mm_llm
        self.retriever = SemanticRetriever(embedding=self.context.embedding, xpathed_only=False)
        print(f"Ready to generate tests on {self.url} for {self.feature_file_content}")

    def _setup_file_paths(self):
        self.feature_file_name = os.path.basename(self.feature_file_path)
        self.code_file_name = f"{self.feature_file_name.replace('.feature', '')}{'_llm' if self.full_llm else '_no_llm'}.py"
        self.final_pytest_path = os.path.join(self.generated_dir, self.code_file_name)
        self.final_feature_path = os.path.join(
            self.generated_dir, self.feature_file_name
        )

    def generate(self):
        start_time = time.time()
        logs, html = self._run_lavague_agent()
        html_chunks = self.retriever.retrieve(self.scenario.expect[0], [html])

        # start timer and spinner for pytest generation
        spinner = yaspin(Spinners.arc, text="Generating pytest...")
        spinner.start()
        if self.full_llm:
            actions, screenshot = self._process_logs(logs)
            prompt = self._build_prompt(html_chunks, actions)
            code = self._generate_pytest(prompt, screenshot)
        else:
            assert_code = self._generate_assert_code(
                self.scenario.expect[0], html_chunks
            )
            code = self._build_pytest_file(logs, assert_code)
            
        self._write_files(code)
        
        # end timer and spinner
        spinner.stop()
        end_time = time.time()
        execution_time = end_time - start_time
        print(build_run_summary(logs, self.final_pytest_path, self.final_feature_path, execution_time))

    def _run_lavague_agent(self):
        selenium_driver = SeleniumDriver(headless=self.headless)
        action_engine = ActionEngine.from_context(context=self.context, driver=selenium_driver)
        world_model = WorldModel.from_context(context=self.context)
        agent = WebAgent(world_model, action_engine, token_counter=self.token_counter)

        agent.get(self.url)
        time.sleep(1)

        if self.full_llm:
            objective = f"Run these scenarios step by step. Make sure you complete each step: {self.feature_file_content}"
            agent.run(objective, log_to_db=self.log_to_db)
        else:
            agent.prepare_run()
            for step in self.scenario.steps:
                agent.run_step(step)
            scenario_completion = agent.run_step(" and ".join(self.scenario.expect))
            if scenario_completion:
                print("Scenario completed successfully", scenario_completion.output)
            else:
                print("Scenario might not be completed")

        return agent.logger.return_pandas(), selenium_driver.get_html()

    def _process_logs(self, logs):
        logs["action"] = logs["code"].dropna().apply(remove_comments)
        cleaned_logs = logs[["instruction", "action"]].fillna("")
        actions = "\n\n".join(
            cleaned_logs["instruction"] + " " + cleaned_logs["action"]
        )
        last_screenshot = SimpleDirectoryReader(
            logs.iloc[-1]["screenshots_path"]
        ).load_data()
        return actions, last_screenshot

    def _build_prompt(self, nodes, actions):
        return FULL_PROMPT_TEMPLATE.format(
            feature_file_name=self.feature_file_name,
            url=self.url,
            feature_file_content=self.feature_file_content,
            expect=self.scenario.expect[0],
            nodes=nodes,
            actions=actions,
        )

    def _generate_pytest(self, prompt, screenshot):
        code = self.mm_llm.complete(prompt, image_documents=screenshot).text
        return clean_llm_output(code)

    def _generate_assert_code(self, expect: str, html_chunks: str) -> str:
        prompt = ASSERT_ONLY_PROMPT_TEMPLATE.format(
            expect=expect,
            html_chunks=html_chunks,
        )
        code = self.llm.complete(prompt).text
        code = code.replace("```python", "").replace("```", "")
        code = code.replace("# assert code here", "")
        return "\n".join([INDENT + l for l in code.splitlines()])

    def _build_pytest_file(self, logs, assert_code):
        pytest_code = self._generate_pytest_header()
        pytest_code += self._generate_given_steps()
        pytest_code += self._generate_when_steps(logs)
        pytest_code += self._generate_then_step(assert_code)
        return pytest_code

    def _generate_pytest_header(self):
        return f"""
import pytest
from pytest_bdd import scenarios, given, when, then
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Constants
BASE_URL = '{self.url}'

# Scenarios
scenarios('{self.feature_file_name}')

# Fixtures
@pytest.fixture
def browser():
    driver = WebDriver()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# Steps
"""

    def _generate_given_steps(self):
        given_steps = ""
        for index, setup in enumerate(self.scenario.context):
            step = setup.replace("'", "\\'")
            method_name = to_snake_case(setup)
            code = "browser.get(BASE_URL)" if index == 0 else "pass"
            given_steps += f"""
@given('{step}')
def {method_name}(browser: WebDriver):
    {code}
"""
        return given_steps

    def _generate_when_steps(self, logs):
        when_steps = ""
        for index, row in logs.iterrows():
            if index < len(self.scenario.steps):
                gherkin_step = self.scenario.steps[index]
                when_steps += self._get_pytest_when(
                    gherkin_step, row["engine"], row["code"], row["instruction"]
                )
        return when_steps

    def _get_pytest_when(
        self, gherkin_step: str, engine: str, engine_log: str, instruction: str
    ) -> str:
        step = gherkin_step.replace("'", "\\'")
        method_name = to_snake_case(gherkin_step)
        if engine == "Navigation Engine":
            actions = yaml.safe_load(engine_log)[0]["actions"]
            actions_code = (
                "\n".join([INDENT + get_nav_action_code(a["action"]) for a in actions])
                or INDENT_PASS
            )
        elif engine == "Navigation Controls":
            actions_code = INDENT + get_nav_control_code(instruction)
        else:
            actions_code = INDENT_PASS
        return f"""
@when('{step}')
def {method_name}(browser: WebDriver):
{actions_code}
    """

    def _generate_then_step(self, assert_code):
        step = self.scenario.expect[0].replace("'", "\\'")
        method_name = to_snake_case(self.scenario.expect[0])
        return f"""
@then('{step}')
def {method_name}(browser: WebDriver):
{assert_code}
"""

    def _write_files(self, code):
        os.makedirs(self.generated_dir, exist_ok=True)
        with open(self.final_feature_path, "w") as file:
            file.write(self.feature_file_content)
        with open(self.final_pytest_path, "w") as file:
            file.write(code)

    @staticmethod
    def _read_scenarios(feature_file_path: str) -> Tuple[List[Scenario], str]:
        scenarios: List[Scenario] = []
        with open(feature_file_path, "r", encoding="utf8") as file:
            feature_file_content = file.read()
            parser = Parser()
            parsed_feature = parser.parse(feature_file_content)
            parsed_scenarios = parsed_feature["feature"]["children"]

            for parsed_scenario in parsed_scenarios:
                scenario = Scenario(parsed_scenario["scenario"]["name"])
                scenarios.append(scenario)
                last_keyword: str = None

                for step in parsed_scenario["scenario"]["steps"]:
                    keyword = step["keywordType"]
                    if keyword == "Conjunction":
                        keyword = last_keyword
                    else:
                        last_keyword = keyword

                    if keyword == "Context":
                        scenario.context.append(step["text"])
                    elif keyword == "Action":
                        scenario.steps.append(step["text"])
                    elif keyword == "Outcome":
                        scenario.expect.append(step["text"])
                    else:
                        print("Parser missing", step)

        return scenarios, feature_file_content


if __name__ == "__main__":
    pytest_generator = TestGenerator(
        "https://google.fr/",
        "./features/demo_dev.feature",
        full_llm=False,
        headless=False,
        log_to_db=True,
    )
    pytest_generator.generate()

# TODO:
# code:
# - add contexts + tokencounter ?
# - add a little bit of telemetry to understand if people are using the CLI ?
# what about the function in utils ? what's the risk of drifting away from the core lavague code if we add actions, change the ways we handle actions, etc ?

# limitations:
# - can only handle one scenario
# - can't handle `switch_to` when running without full_llm
# - saves the feature file to ./generated_tests/ along with the code so that a user can easily run `pytest` on the generated test


# examples:
# make sure all are in english with EN urls ?
# - issues: amazon.com has a captcha, .fr doesn't

# docs:
# add new section in side bar
# - get started, installation, usage, walkthrouhg ?
# - index of docs
# - main readme.md
