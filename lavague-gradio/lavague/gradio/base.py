from io import BytesIO
import queue
from typing import List, Optional
from lavague.core.agents import WebAgent
import gradio as gr
from PIL import Image


class GradioAgentDemo:
    """
    Launch an agent gradio demo of lavague

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
            max-height: 3rem !important;
            max-width: 5rem !important;
            min-width: min(100px,100%) !important;
    }
    """

    title = """
    <div class='parent' align="center">
    <div class='child' style="display: inline-block !important;">
    <img src="https://raw.githubusercontent.com/lavague-ai/LaVague/new_gradio/docs/assets/logo.png" width=40px/>
    </div>
    <div class='child' style="display: inline-block !important;">
    <h1>LaVague</h1>
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
        agent: WebAgent,
        user_data=None,
        screenshot_ratio: float = 1,
    ):
        self.objective = objective
        self.instructions = instructions
        self.agent = agent
        self.user_data = user_data
        self.previous_val = None
        self.screenshot_ratio = screenshot_ratio

    def _init_driver(self):
        def init_driver_impl(url, img):
            self.agent.action_engine.driver.get(url)

            ret = self.agent.action_engine.driver.get_screenshot_as_png()
            ret = BytesIO(ret)
            ret = Image.open(ret)
            img = ret
            return url, img

        return init_driver_impl

    def _process_instructions(self):
        def process_instructions_impl(objective, url_input, image_display, history):
            msg = gr.ChatMessage(
                role="assistant", content="⏳ Thinking of next steps..."
            )
            history.append(msg)
            yield objective, url_input, image_display, history
            self.agent.action_engine.set_gradio_mode_all(
                True, objective, url_input, image_display, history
            )
            self.agent.clean_screenshot_folder = False
            yield from self.agent._run_demo(
                objective,
                self.user_data,
                False,
                objective,
                url_input,
                image_display,
                history,
                self.screenshot_ratio,
            )
            return objective, url_input, image_display, history

        return process_instructions_impl

    def __add_message(self):
        def add_message(history, message):
            history.clear()
            return history

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
            with gr.Tab(""):
                with gr.Row():
                    gr.HTML(self.title)

                with gr.Row(equal_height=False):
                    with gr.Column():
                        with gr.Row():
                            with gr.Tabs(
                                selected=1
                                if self.agent.action_engine.driver.get_url() is not None
                                else 0
                            ) as tabs:
                                with gr.Tab("URL", id=0):
                                    url_input = gr.Textbox(
                                        value=self.agent.action_engine.driver.get_url(),
                                        scale=9,
                                        type="text",
                                        label="Enter URL and press 'Enter' to load the page.",
                                        visible=True,
                                        max_lines=1,
                                    )
                                with gr.Tab("Objective", id=1) as tab:
                                    objective_input = gr.Textbox(
                                        value=self.objective,
                                        scale=9,
                                        type="text",
                                        label="Enter the objective and press 'Enter' to start processing it.",
                                        visible=True,
                                        max_lines=1,
                                    )
                with gr.Row(variant="panel", equal_height=True):
                    with gr.Column(scale=8):
                        image_display = gr.Image(
                            label="Browser", interactive=False, height="100%"
                        )
                    with gr.Column(scale=2):
                        chatbot = gr.Chatbot(
                            [],
                            label="Agent output",
                            elem_id="history",
                            type="messages",
                            bubble_full_width=False,
                            height="100%",
                            placeholder="Agent output will be shown here\n",
                            layout="bubble",
                        )
                # objective submission handling
                objective_input.submit(
                    self.__add_message(),
                    inputs=[chatbot, objective_input],
                    outputs=[chatbot],
                ).then(
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
                )
                # Use the image_updater generator function
                # submission handling
                url_input.submit(
                    self._init_driver(),
                    inputs=[url_input, image_display],
                    outputs=[url_input, image_display],
                )
                if self.agent.driver.get_url() is not None:
                    demo.load(
                        fn=self.refresh_img_dislay,
                        inputs=[url_input, image_display],
                        outputs=[url_input, image_display],
                        show_progress=False,
                    )
        demo.launch(server_port=server_port, share=True, debug=True)
