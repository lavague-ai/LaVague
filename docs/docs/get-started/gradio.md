# LaVague Gradio Agent Demo

### What is LaVague's Gradio Agent Demo?

Our agents have a `demo` method, which will launch an interactive demo which we can access by clicking on the public or local URL generated. 

We can use this `demo mode` to can interact with LaVague in our browser, testing out various different objectives on different URLs and viewing the Agent's progress and output in a chat user interface.

You can take a quick look at this feature in the video below:

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="https://github.com/lavague-ai/LaVague/blob/gradio_new/docs/assets/gradio.webm?raw=true" type="video/webm">
  </video>
</figure>

### How to launch a LaVague Agent demo

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/notebooks/Gradio.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open code example in Colab"></a>

TO get started with our `demo` mode, you will firstly need to install the `lavague-gradio` package (as well as the `lavague` package): 

```bash
pip install lavague lavague-gradio
```

If you already had the `lavague` package installed, make sure your driver package is on the latest version to avoid compatibility issues:
```bash
pip install --upgrade lavague-drivers-selenium
```

You can now use the same code as you would when [getting started with our agent](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/) in the standard way, but we replace the `agent.run()` method with our `agent.demo()` method.

```python
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

selenium_driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine)

# Set our URL
agent.get("https://huggingface.co/docs")

# Launch our demo with our objective
agent.demo("Go on the quicktour of PEFT")
```

### Optional arguments

The `agent.run()` has the two following optional arguments:

- objective: A string objective that will pre-populate the objective on the Gradio demo
- user_data: Any input data you want to pass to the agent, such as the data to be used for filling in an application form