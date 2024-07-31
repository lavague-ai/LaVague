from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.retrievers import SemanticRetriever
from lavague.drivers.selenium import SeleniumDriver

# from selenium.webdriver.chrome.options import Options
# from llama_index.llms.openai import OpenAI
from llama_index.llms.openai import OpenAI

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.legacy.readers.file.base import SimpleDirectoryReader
import yaml
from llama_index.embeddings.openai import OpenAIEmbedding

from lavague.qa.utils import (
    remove_comments,
    clean_llm_output,
    to_snake_case,
    get_nav_action_code,
    get_nav_control_code,
    INDENT,
    INDENT_PASS,
)
from lavague.qa.prompts import FULL_PROMPT_TEMPLATE, ASSERT_ONLY_PROMPT_TEMPLATE
from yaspin import yaspin
from yaspin.spinners import Spinners
import time
from gherkin.parser import Parser
from typing import List

from lavague.core.retrievers import SemanticRetriever
from llama_index.core import QueryBundle
import os


class TestGenerator:
    def __init__(
        self,
        url: str,
        feature_file_path: str,
        full_llm: bool,
        headless: bool,
        log_to_db: bool,
    ):
        self.url = url
        self.feature_file_path = feature_file_path
        self.scenarios, self.feature_file_content = read_scenarios(feature_file_path)
        self.scenario = self.scenarios[0]

        self.full_prompt_template = FULL_PROMPT_TEMPLATE
        self.assert_only_prompt_template = ASSERT_ONLY_PROMPT_TEMPLATE

        self.full_llm = full_llm

        self.feature_file_name = os.path.basename(feature_file_path)
        self.code_file_name = self.feature_file_name.replace(".feature", ".py")

        self.headless = headless
        self.log_to_db = log_to_db

        self.generated_dir = "./generated_tests"
        self.final_pytest_path = f"{self.generated_dir}/{self.code_file_name}"
        self.final_feature_path = f"{self.generated_dir}/{self.feature_file_name}"

        self.mm_llm = OpenAIMultiModal("gpt-4o", max_new_tokens=1000)
        self.llm = OpenAI(model="gpt-4o")

        self.embedding = OpenAIEmbedding(model="text-embedding-3-small")
        self.retriever = SemanticRetriever(embedding=self.embedding, xpathed_only=False)

        print(
            f"Ready to generate tests on {self.url} for {self.feature_file_path} {self.feature_file_content}"
        )

    def generate(self):
        logs, html = self.run_lavague_agent()
        html_chunks = self.retrieve_chunks(self.scenario.expect[0], html)

        code = ""
        if self.full_llm:
            actions, screenshot = self.process_logs(logs)
            prompt = self.build_prompt(html_chunks, actions)
            code = self.generate_pytest(prompt, screenshot)
        else:
            assert_code = self.generate_assert_code(
                self.scenario.expect[0], html_chunks
            )
            print(f"Assert code: {assert_code}")
            code = self.build_pytest_file(logs, assert_code)
            print(f"Pytest code: {code}")

        self.write_files(code)
        print(
            f"\nTests successfully generated\n - Run `pytest {self.final_pytest_path}` to run the generated test."
        )

    @yaspin(
        Spinners.arc,
        text="Generating pytest file from actions...",
        timer=True,
        color="green",
    )
    def build_pytest_file(self, logs, assert_code):
        pytest_code = f"""
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
        # GENERATE @given
        is_first = True
        for setup in self.scenario.context:
            step = setup.replace("'", "\\'")
            method_name = to_snake_case(setup)
            if is_first:
                is_first = False
                code = "browser.get(BASE_URL)"
            else:
                code = "pass"
            pytest_code += f"""
@given('{step}')
def {method_name}(browser: WebDriver):
    {code}
"""

        # GENERATE @when
        for index, row in logs.iterrows():
            if index < len(self.scenario.steps):
                gherkin_step = self.scenario.steps[index]
                pytest_code += self.get_pytest_when(
                    gherkin_step, row["engine"], row["code"], row["instruction"]
                )

        step = self.scenario.expect[0].replace("'", "\\'")
        method_name = to_snake_case(self.scenario.expect[0])
        pytest_code += f"""
@then('{step}')
def {method_name}(browser: WebDriver):
{assert_code}
"""

        return pytest_code

    def get_pytest_when(
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

    @yaspin(Spinners.arc, text="Generating assert code...", timer=True, color="green")
    def generate_assert_code(self, expect: str, html_chunks: str) -> str:
        prompt = f"""You are an expert in software testing frameworks and Python code generation. You answer in python markdown only and nothing else.
Your only goal is to use the provided Gherkin and HTML nodes to generate a valid pytest-bdd python assert statement. 
- Include all necessary imports and fixtures.
- If element selection is needed, prefer XPath based on class or text content to fetch it. 
- You answer in python code only and nothing else.
- You have access to a browser variable of type selenium.webdriver.chrome.webdriver.Chrome

```python
browser: WebDriver
# assert code here
```

I will provide an example below:
----------
Gherkin: Then the cost should be "34,70 €"
HTML: <div><span>Cost:</span><span class="calculator__cta__price">34,70 €</span></div>
                
Resulting pytest code: 
cost_element = WebDriverWait(browser, 10).until(
    EC.presence_of_element_located((By.XPATH, "//span[@class='calculator__cta__price']"))
)
actual_cost = cost_element.text.strip()
assert actual_cost == expected_cost

----------
Given this information, generate a valid pytest-bdd assert instruction with the following inputs:
Gherkin expect of the feature to be tested: Then {expect}\n
Potentially relevant HTML that you may use to help you generate the assert code: {html_chunks}\n
    """
        code = self.llm.complete(prompt).text
        code = code.replace("```python", "").replace("```", "")
        code = code.replace("# assert code here", "")
        return "\n".join([INDENT + l for l in code.splitlines()])

    # run scenarios and return the logs as a dataframe
    @yaspin(Spinners.arc, text="Running agent...", timer=True, color="blue")
    def run_lavague_agent(self):
        selenium_driver = SeleniumDriver(headless=self.headless)
        world_model = WorldModel()
        action_engine = ActionEngine(selenium_driver)
        agent = WebAgent(world_model, action_engine)

        print(self.scenario.expect)

        # load the URL
        agent.get(self.url)
        time.sleep(1)

        if self.full_llm:
            objective = f"Run these scenarios step by step. Make sure you complete each step: {self.feature_file_content}"
            agent.run(objective, log_to_db=self.log_to_db)
        else:
            agent.prepare_run()

            for step in self.scenario.steps:
                time.sleep(1)
                agent.run_step(step)

            # We run the asserts, the agent should COMPLETE
            scenario_completion = agent.run_step(" and ".join(self.scenario.expect))
            if scenario_completion:
                print("Scenario completed successfully", scenario_completion.output)
            else:
                print("Scenario might not be completed")

        # retrieve logs
        logs = agent.logger.return_pandas()
        return logs, selenium_driver.get_html()

    def retrieve_chunks(self, expect, html):
        return self.retriever.retrieve(QueryBundle(expect), [html])

    @yaspin(Spinners.arc, text="Processing logs...", color="green")
    def process_logs(self, logs):
        logs["action"] = logs["code"].dropna().apply(remove_comments)
        cleaned_logs = logs[["instruction", "action"]].fillna("")
        actions = "\n\n".join(
            cleaned_logs["instruction"] + " " + cleaned_logs["action"]
        )
        last_screenshot = SimpleDirectoryReader(
            logs.iloc[-1]["screenshots_path"]
        ).load_data()
        return actions, last_screenshot

    @yaspin(Spinners.arc, text="Building prompt...", color="green")
    def build_prompt(self, nodes, actions):
        prompt = self.full_prompt_template.format(
            feature_file_name=self.feature_file_name,
            url=self.url,
            feature_file_content=self.feature_file_content,
            expect=self.scenario.expect[0],
            nodes=nodes,
            actions=actions,
        )
        # prompt += f"Feature file name: {self.feature_file_name}\n\nURL: {self.url}\n\nGherkin of the feature to be tested:\n{self.feature_file_content}\n\nAssert statement: {self.scenario.expect}\n\nPotentially relevant nodes that you may use to help you generate the assert code: {nodes}\n\nList of already executed instructions and actions:\n{actions}\n"
        return prompt

    @yaspin(
        Spinners.arc,
        text="Generating pytest file with LLMs...",
        timer=True,
        color="green",
    )
    def generate_pytest(self, prompt, screenshot):
        code = self.mm_llm.complete(prompt, image_documents=screenshot).text
        return clean_llm_output(code)

    @yaspin(Spinners.arc, text="Writing files...", color="green")
    def write_files(self, code):
        try:
            if not os.path.exists(self.generated_dir):
                os.makedirs(self.generated_dir)
                print(f"\nDirectory {self.generated_dir} created successfully.")
        except OSError as error:
            print(f"\nError creating directory {self.generated_dir}: {error}")

        with open(self.final_feature_path, "w") as file:
            print(f"\n- pytest: {self.final_feature_path}")
            file.write(self.feature_file_content)

        with open(self.final_pytest_path, "w") as file:
            print(f"- feature: {self.final_pytest_path}")
            file.write(code)


class Scenario:
    def __init__(self, name: str) -> None:
        self.name = name
        self.context: List[str] = []
        self.steps: List[str] = []
        self.expect: List[str] = []

    def __str__(self) -> str:
        return f"Context: {self.context}\nSteps: {self.steps}\nExpect: {self.expect}"

    def __repr__(self) -> str:
        return f"Scenario({str(self)})"


# TODO: note -> modified to also return the full contents
def read_scenarios(feature_file_path: str) -> List[Scenario]:
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
    pytest_generator = TestGenerator("https://amazon.fr/", "./features/demo_amazon.feature", full_llm=True, headless=False, log_to_db=True)
    pytest_generator.generate()

