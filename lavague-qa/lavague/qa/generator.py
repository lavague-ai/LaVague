from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.core.retrievers import SemanticRetriever
from lavague.drivers.selenium import SeleniumDriver

# from selenium.webdriver.chrome.options import Options
# from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.legacy.readers.file.base import SimpleDirectoryReader

from lavague.qa.utils import remove_comments, clean_llm_output
from lavague.qa.prompts import EXAMPLE_PROMPT
from yaspin import yaspin
from yaspin.spinners import Spinners
import time


import os


class TestGenerator:
    def __init__(self, url: str, feature: str, headless: bool, log_to_db: bool):
        self.url = url
        self.feature = feature
        self.headless = headless
        self.log_to_db = log_to_db

        self.feature_file_name = os.path.basename(feature)
        self.code_file_name = self.feature_file_name.replace(".feature", ".py")

        self.generated_dir = "./generated_tests"
        self.final_pytest_path = f"{self.generated_dir}/{self.code_file_name}"
        self.final_feature_path = f"{self.generated_dir}/{self.feature_file_name}"

        self.feature_contents, self.assert_statements = self.parse_feature_file()

        self.mm_llm = OpenAIMultiModal("gpt-4o", max_new_tokens=1000)
        self.prompt = EXAMPLE_PROMPT

        print(
            f"Ready to generate tests on {self.url} for {self.feature} {self.feature_contents}"
        )

    def generate(self):
        logs, nodes = self.run_lavague_agent()
        actions, screenshot = self.process_logs(logs)
        prompt = self.build_prompt(nodes, actions)
        code = self.generate_pytest(prompt, screenshot)
        self.write_files(code)
        print(
            f"\nTests successfully generated\n - Run `pytest {self.code_file_name}` to run the generated test."
        )

    @yaspin(Spinners.arc, text="Parsing feature file...", color="green")
    def parse_feature_file(self):
        file_contents = ""
        with open(self.feature, "r") as file:
            file_contents = file.read()
        scenarios = file_contents.split("Scenario:")

        assert_statements = []
        for scenario in scenarios[
            1:
        ]:  # skip first split which is the feature description
            steps = scenario.strip().split("\n")[1:]  # skip name of scenario
            if steps:  # Check if there are any steps
                assert_statements.append(steps[-1].strip())

        return file_contents, assert_statements

    # run scenarios and return the logs as a dataframe
    # Function decorator:
    @yaspin(Spinners.arc, text="Running agent...", timer=True, color="blue")
    def run_lavague_agent(self):
        selenium_driver = SeleniumDriver(headless=self.headless)
        world_model = WorldModel()
        action_engine = ActionEngine(selenium_driver)
        agent = WebAgent(world_model, action_engine)

        # load the URL
        agent.get(self.url)
        time.sleep(1)

        # run agent
        objective = f"Run these scenarios step by step. Make sure you complete each step: {self.feature_contents}"
        agent.run(objective, log_to_db=self.log_to_db)
        # retrieve logs
        logs = agent.logger.return_pandas()

        # extract nodes for asserts
        retriever = SemanticRetriever(
            embedding=action_engine.python_engine.embedding, xpathed_only=False
        )
        html = selenium_driver.get_html().splitlines()
        nodes = retriever.retrieve(f"{self.assert_statements}", html)

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
        ).load_data()  # load last screenshot taken
        return actions, last_screenshot

    @yaspin(Spinners.arc, text="Building prompt...", color="green")
    def build_prompt(self, nodes, actions):
        prompt = EXAMPLE_PROMPT
        prompt += f"Feature file name: {self.feature_file_name}\n\nURL: {self.url}\n\nGherkin of the feature to be tested:\n{self.feature_contents}\n\nAssert statement: {self.assert_statements}\n\nPotentially relevant nodes that you may use to help you generate the assert code: {nodes}\n\nList of already executed instructions and actions:\n{actions}\n"
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
            file.write(self.feature_contents)

        with open(self.final_pytest_path, "w") as file:
            print(f"- feature: {self.final_pytest_path}")
            file.write(code)
