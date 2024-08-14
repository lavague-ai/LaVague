from io import BytesIO
import os
from typing import List, Optional, Tuple
from lavague.contexts.openai.base import OpenaiContext
from lavague.core.agents import WebAgent
import gradio as gr
from lavague.core.memory import ShortTermMemory
from lavague.core.retrievers import SemanticRetriever
from lavague.core.world_model import WorldModel
from lavague.qa.generator import Scenario, TestGenerator
from lavague.drivers.selenium import SeleniumDriver, BrowserbaseRemoteConnection
from lavague.core.action_engine import ActionEngine
from PIL import Image
from gherkin.parser import Parser
from urllib.parse import urlparse


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


class GradioQADemo:
    """
    Launch an agent gradio demo of lavague-qa

    Args:
        driver (`BaseDriver`):
            The driver
        context (`ActionContext`):
            An action context
    """

    html = """
    <div class="list-container">
        <ul>
        </ul>
    </div>
    """

    css = """
        .my-button {
            height: 100px; /* Increase the height of the buttons */
            width: 100%; /* Make sure the button takes the full width */
            max-width: 300px; /* Optional: set a max width */
            max-height: 80px;
            font-size: 1.1rem; /* Increase font size */
        }
        .button-container {
            display: flex;
            justify-content: center; /* Center buttons horizontally */
            align-items: center; /* Center buttons vertically */
            height: 100%; /* Ensure it takes up the full height */
            width: 100%; /* Ensure it takes up the full width */
        }
    """

    title = """
    <div class='parent' align="center">
    <div class='child' style="display: inline-block !important;">
    <img src="https://raw.githubusercontent.com/lavague-ai/LaVague/new_gradio/docs/assets/logo.png" width=40px/>
    </div>
    <div class='child' style="display: inline-block !important;">
    <h1>LaVague - QA</h1>
    </div>
    </div>
    """

    title_history = """
    <div align="center">
    <h3>Steps</h3>
    </div>
    """

    def __init__(
        self,
        objective: str,
        instructions: Optional[List[str]],
        agent: WebAgent = None,
        user_data=None,
        screenshot_ratio: float = 1,
        use_browserbase=False,
    ):
        self.use_browserbase = use_browserbase
        self.objective = objective
        self.instructions = instructions
        self.agent = agent
        self.user_data = user_data
        self.previous_val = None
        self.screenshot_ratio = screenshot_ratio
        self.api_key = ""
        self.retriever = None
        self.scenarios = None
        self.feature_file_content = None
        self.scenario = None
        self.llm = None
        self.code = ""

    @staticmethod
    def _read_scenarios(gherkin: str) -> Tuple[List[Scenario], str]:
        scenarios: List[Scenario] = []
        feature_file_content = gherkin
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

    def _fill_example(self, file: str, url: str):
        def fill_example_impl():
            file_str = open("features/" + file, "r")
            objective = file_str.read()
            url_input = url
            return url_input, objective

        return fill_example_impl

    def _show_code(self):
        def show_code_impl(browser: gr.Image, code: gr.Markdown):
            browser = gr.Image(
                label="Browser", interactive=False, height="100%", visible=False
            )
            code = gr.Markdown(visible=True, value=self.code)
            return browser, code

        return show_code_impl

    def _init_driver(self):
        def init_driver_impl(url, img, api_key):
            if len(api_key) == 0 and os.getenv("OPENAI_API_KEY") is None:
                raise gr.Error("An OpenAI API Key is needed to run the agent.")
            elif not uri_validator(url):
                raise gr.Error("Please specify a valid URL.")
            else:
                if self.use_browserbase:
                    browserbase_connection = BrowserbaseRemoteConnection(
                        "http://connect.browserbase.com/webdriver",
                        api_key=os.environ["BROWSERBASE_API_KEY"],
                        project_id=os.environ["BROWSERBASE_PROJECT_ID"],
                    )
                    selenium_driver = SeleniumDriver(
                        remote_connection=browserbase_connection
                    )
                if self.agent is None:
                    if self.use_browserbase == False:
                        selenium_driver = SeleniumDriver(headless=True)
                    openai_content = OpenaiContext(
                        api_key=api_key if len(api_key) > 0 else None
                    )
                    openai_content.mm_llm.max_new_tokens = 2000
                    self.llm = openai_content.llm
                    self.retriever = SemanticRetriever(
                        embedding=openai_content.embedding, xpathed_only=False
                    )
                    action_engine = ActionEngine.from_context(
                        context=openai_content, driver=selenium_driver
                    )
                    world_model = WorldModel.from_context(context=openai_content)
                    agent = WebAgent(world_model, action_engine)
                    agent.set_origin("lavague-qa-gradio-hf")
                    self.agent = agent

                if self.use_browserbase:
                    self.agent.driver = selenium_driver

                self.agent.get(url)
                ret = self.agent.action_engine.driver.get_screenshot_as_png()
                ret = BytesIO(ret)
                ret = Image.open(ret)
                img = ret
                return url, img

        return init_driver_impl

    def _process_instructions(self):
        def process_instructions_impl(objective, url_input, image_display, history):
            original_url = url_input
            self.scenarios, self.feature_file_content = self._read_scenarios(objective)
            self.scenario = self.scenarios[0]
            msg = gr.ChatMessage(
                role="assistant", content="⏳ Thinking of next steps..."
            )
            history.append(msg)
            yield objective, url_input, image_display, history
            self.agent.action_engine.set_gradio_mode_all(
                True, objective, url_input, image_display, history
            )
            self.agent.clean_screenshot_folder = False
            self.agent.st_memory = ShortTermMemory()
            self.agent.prepare_run()
            nb_steps = 1
            for index, step in enumerate(self.scenario.steps):
                yield from self.agent._run_step_gradio(
                    step, index, objective, url_input, image_display, history
                )
                nb_steps = index
            yield from self.agent._run_step_gradio(
                " and ".join(self.scenario.expect),
                nb_steps,
                objective,
                url_input,
                image_display,
                history,
            )
            if self.agent.result:
                history[-1] = gr.ChatMessage(
                    role="assistant",
                    content=f"{self.agent.result.output}",
                    metadata={"title": f"Scenario completed successfully"},
                )
            else:
                history[-1] = gr.ChatMessage(
                    role="assistant",
                    content="",
                    metadata={"title": f"Scenario might not be completed"},
                )
            history.append(
                gr.ChatMessage(
                    role="assistant",
                    content="The Pytest code is currently generated.",
                    metadata={"title": f"Generating Pytest..."},
                )
            )
            yield (
                objective,
                url_input,
                image_display,
                history,
            )
            logs = self.agent.logger.return_pandas()
            html = self.agent.driver.get_html()
            html_chunks = self.retriever.retrieve(self.scenario.expect[0], [html])
            assert_code = TestGenerator._generate_assert_code(
                self.scenario.expect[0], html_chunks, self.llm
            )
            code = TestGenerator._build_pytest_file(
                logs, assert_code, self.scenario, original_url, "gradio.gherkin"
            )
            self.code = "```python" + code + "```"

            history[-1] = gr.ChatMessage(
                role="assistant",
                content="The code is ready to use.",
                metadata={"title": f"PyTest generated"},
            )
            yield (
                objective,
                url_input,
                image_display,
                history,
            )
            if self.use_browserbase:
                self.agent.driver.destroy()
            return objective, url_input, image_display, history

        return process_instructions_impl

    def __add_message(self):
        def add_message(history, message, browser: gr.Image, code_display: gr.Markdown):
            browser = gr.Image(
                label="Browser", interactive=False, height="100%", visible=True
            )
            code = gr.Markdown(visible=False, value="")
            history.clear()
            return history, browser, code

        return add_message

    def refresh_img_dislay(self, url, image_display):
        img = self.agent.driver.get_screenshot_as_png()
        img = BytesIO(img)
        img = Image.open(img)
        if self.screenshot_ratio != 1:
            img = img.resize(
                (
                    int(img.width / self.screenshot_ratio),
                    int(img.height / self.screenshot_ratio),
                )
            )
        image_display = img
        return url, image_display

    def launch(self, server_port=7860, share=True, debug=True):
        with gr.Blocks(
            gr.themes.Default(primary_hue="blue", secondary_hue="neutral"), css=self.css
        ) as demo:
            with gr.Tab("Agent - QA"):
                with gr.Row():
                    gr.HTML(self.title)

                with gr.Row(variant="panel", equal_height=True):
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(scale=8):
                                url_input = gr.Textbox(
                                    scale=8,
                                    type="text",
                                    label="Enter URL and press 'Enter' to load the page.",
                                    visible=True,
                                    max_lines=1,
                                    interactive=True,
                                )
                                with gr.Row():
                                    txt = gr.Markdown("## Example scenarios: ")
                                with gr.Row():
                                    with gr.Blocks(
                                        elem_id="button-container", fill_height=True
                                    ):
                                        ex1 = gr.Button(
                                            "Wikipedia's login",
                                            elem_classes="my-button",
                                        )
                                        ex2 = gr.Button(
                                            "Amazon cart feature",
                                            elem_classes="my-button",
                                        )
                                        ex3 = gr.Button(
                                            "Navigation on HSBC",
                                            elem_classes="my-button",
                                        )
                                        ex1.click()
                            with gr.Column(scale=2):
                                objective_input = gr.Textbox(
                                    value=self.objective,
                                    scale=2,
                                    type="text",
                                    label="Enter here your Gherkin",
                                    visible=True,
                                    lines=5,
                                    max_lines=5,
                                    interactive=True,
                                )
                                send_btn = gr.Button("Launch agent")

                with gr.Row(variant="panel", equal_height=True):
                    with gr.Column(scale=8):
                        image_display = gr.Image(
                            label="Browser", interactive=False, height="100%"
                        )
                        code_display = gr.Markdown(visible=False)
                    with gr.Column(scale=2):
                        chatbot = gr.Chatbot(
                            [],
                            label="QA output",
                            elem_id="history",
                            type="messages",
                            bubble_full_width=False,
                            height="100%",
                            placeholder="QA output will be shown here\n",
                            layout="bubble",
                        )
            with gr.Tab("API keys"):
                api_key = gr.Textbox(
                    value="",
                    type="text",
                    label="Please write your OpenAI API Key here",
                    visible=True,
                    max_lines=1,
                    interactive=True,
                )

            send_btn.click(
                self.__add_message(),
                inputs=[chatbot, objective_input, image_display, code_display],
                outputs=[chatbot, image_display, code_display],
            ).then(
                self._init_driver(),
                inputs=[url_input, image_display, api_key],
                outputs=[url_input, image_display],
            ).success(
                self._process_instructions(),
                inputs=[
                    objective_input,
                    url_input,
                    image_display,
                    chatbot,
                ],
                outputs=[
                    objective_input,
                    url_input,
                    image_display,
                    chatbot,
                ],
            ).then(
                self._show_code(),
                inputs=[image_display, code_display],
                outputs=[image_display, code_display],
            )
            url_input.submit(
                self._init_driver(),
                inputs=[url_input, image_display, api_key],
                outputs=[url_input, image_display],
            )
            ex1.click(
                fn=self._fill_example(
                    "demo_wikipedia.feature", "https://en.wikipedia.org"
                ),
                inputs=[],
                outputs=[url_input, objective_input],
            )
            ex2.click(
                fn=self._fill_example("demo_amazon.feature", "https://amazon.fr"),
                inputs=[],
                outputs=[url_input, objective_input],
            )
            ex3.click(
                fn=self._fill_example("demo_hsbc.feature", "https://www.hsbc.fr/"),
                inputs=[],
                outputs=[url_input, objective_input],
            )

        demo.launch(server_port=server_port, share=True, debug=True)


grad = GradioQADemo("", None, None)
grad.launch()
