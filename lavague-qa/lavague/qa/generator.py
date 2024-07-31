from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.retrievers import SemanticRetriever
from lavague.drivers.selenium import SeleniumDriver

# from selenium.webdriver.chrome.options import Options
# from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.legacy.readers.file.base import SimpleDirectoryReader

from lavague.qa.utils import remove_comments, clean_llm_output
from lavague.qa.prompts import FULL_PROMPT_TEMPLATE, ASSERT_ONLY_PROMPT_TEMPLATE
from yaspin import yaspin
from yaspin.spinners import Spinners
import time
from gherkin.parser import Parser
from typing import List


import os


class TestGenerator:
    def __init__(self, url: str, feature_file_path: str, headless: bool, log_to_db: bool):
        self.url = url
        self.feature_file_path = feature_file_path
        self.scenarios, self.feature_file_content = read_scenarios(feature_file_path)
        self.scenario = self.scenarios[0]
        
        self.full_prompt_template = FULL_PROMPT_TEMPLATE
        self.assert_only_prompt_template = ASSERT_ONLY_PROMPT_TEMPLATE
        
        self.feature_file_name = os.path.basename(feature_file_path)
        self.code_file_name = self.feature_file_name.replace(".feature", ".py")
        
        self.headless = headless
        self.log_to_db = log_to_db

        self.generated_dir = "./generated_tests"
        self.final_pytest_path = f"{self.generated_dir}/{self.code_file_name}"
        self.final_feature_path = f"{self.generated_dir}/{self.feature_file_name}"

        # self.feature_contents, self.assert_statements = self.parse_feature_file()

        self.mm_llm = OpenAIMultiModal("gpt-4o", max_new_tokens=1000)

        print(
            f"Ready to generate tests on {self.url} for {self.feature_file_path} {self.feature_file_content}"
        )

    def generate(self):
        logs, nodes = self.run_lavague_agent()
        actions, screenshot = self.process_logs(logs)
        prompt = self.build_prompt(nodes, actions)
        code = self.generate_pytest(prompt, screenshot)
        self.write_files(code)
        print(
            f"\nTests successfully generated\n - Run `pytest {self.final_pytest_path}` to run the generated test."
        )
        

    # run scenarios and return the logs as a dataframe
    @yaspin(Spinners.arc, text="Running agent...", timer=True, color="blue")
    def run_lavague_agent(self, step_by_step=False):
        selenium_driver = SeleniumDriver(headless=self.headless)
        world_model = WorldModel()
        action_engine = ActionEngine(selenium_driver)
        agent = WebAgent(world_model, action_engine)

        # load the URL
        agent.get(self.url)
        time.sleep(1)
        
        if step_by_step:
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
        else:
            objective = f"Run these scenarios step by step. Make sure you complete each step: {self.feature_file_content}"
            agent.run(objective, log_to_db=self.log_to_db)

        # retrieve logs
        logs = agent.logger.return_pandas()
        
        # extract nodes for asserts TODO: separate
        retriever = SemanticRetriever(
            embedding=action_engine.python_engine.embedding, xpathed_only=False
        )
        html = selenium_driver.get_html().splitlines()
        nodes = retriever.retrieve(f"{self.scenario.expect}", html)

        return logs, nodes
    
    
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
            expect=self.scenario.expect,
            nodes=nodes,
            actions=actions,
        )
        # prompt += f"Feature file name: {self.feature_file_name}\n\nURL: {self.url}\n\nGherkin of the feature to be tested:\n{self.feature_file_content}\n\nAssert statement: {self.scenario.expect}\n\nPotentially relevant nodes that you may use to help you generate the assert code: {nodes}\n\nList of already executed instructions and actions:\n{actions}\n"
        return prompt

    @yaspin(Spinners.arc, text="Generating pytest file...", timer=True, color="green")
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
    with open(feature_file_path, 'r', encoding='utf8') as file:
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
                
                if keyword == 'Context':
                    scenario.context.append(step['text'])
                elif keyword == 'Action':
                    scenario.steps.append(step['text'])
                elif keyword == 'Outcome':
                    scenario.expect.append(step['text'])
                else:
                    print("Parser missing", step)

    return scenarios, feature_file_content