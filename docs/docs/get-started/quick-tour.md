# Quick Tour

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/LaVague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>

!!! tips "Pre-requisites"

    - We use OpenAI's models, for the embedding, LLM and Vision model. You will need to set the OPENAI_API_KEY variable in your local environment with a valid API key for this example to work.

    If you don't have an OpenAI API key, please get one [here](https://platform.openai.com/docs/quickstart/developer-quickstart)

    - Our package currently only supports python versions 3.10 or greater. Please upgrade your python version if you are using a version below this.

## Installation

We start by downloading LaVague.

```bash
pip install lavague
```

!!! tip "OPENAI_API_KEY"
    If you haven't already set a valid OpenAI API Key as the `OPENAI_API_KEY` environment variable in your local environment, you will need to do that now.

## Full code example

Here is a full code example to create and run your agent using LaVague.

We will go over what is happening in this code in the following sections below.

```python
# Install necessary elements
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

# Set up our three key components: Driver, Action Engine, World Model
driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(driver)
world_model = WorldModel()

# Create Web Agent
agent = WebAgent(world_model, action_engine)

# Set URL
agent.get("https://huggingface.co/docs")

# Run agent with a specific objective
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)

You can also launch an interactive Gradio interface for using the agent with the `agent.demo()` method.

```python
# Launch the agent in the Agent Gradio Demo mode
agent.demo("Go on the quicktour of PEFT")
```
You can take a quick look at the `demo` feature in the video below:

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="https://github.com/lavague-ai/LaVague/blob/main/docs/assets/gradio.webm?raw=true" type="video/webm">
  </video>
</figure>

## Key components explained

### Driver

The Driver component is used to perform actions on web browsers and get information about our current web page.

We currently provide a Selenium Driver component by default, as well as a Playwright Driver option.

#### 🍪 Plugging in an existing browser session

You can leverage your cookies of your usual browser session, for example, to avoid bot protections around log-ins for sites you are already logged in to on your browser session, by adding a path to your Chrome profile directory as an argument to `user_data_dir` when initializing your browser. If not supplied, Chrome starts a fresh session.

#### Headless vs non-headless mode

In the code example above, we set`headless` mode to `False`. This means the driver will open a browser on your machine where you can watch in real-time the actions the driver is performing. 

By default, this option is set to `True`, which consumes less resources and can be useful when running LaVague in an environment where you don't have access to the browser and can be combined with passing the `agent.run()` method a `display=True` argument to have screenshots regular displayed so you can still track the browser's progression.

For more information on the Driver component see our [Driver module guide](../learn/browser-drivers.md)

### Action Engine

Next up, let's consider the Action Engine component. This component receives a natural language text instruction and generates the action needed to carry out this instruction. 

In our example, the Action Engine will perform RAG and generates the code for the action using the default embedding and Large Language Models (OpenAI's text-embedding-3-large & GPT-4o). To find out more about the Action Engine and how to use custom models see our [Action Engine guide](../learn/action-engine.md) or [customization guide](./customization.md).

### World Model

The World Model is responsible for converting the user's global objective into the next instruction for the Action Engine to carry out based on visual and textual information.

The World Model uses a multi-modal model to do this conversion. This is GPT-4o by default, but you can try using it with custom models in our [customization guide](./customization.md).

To find out more about the World Model, see our [World Model guide](../learn/world-model.md).

### Web Agent

The Web Agent brings all of these components together and can be used to perform tasks defined by our `objective` argument with the `run` method or to launch an interactive interface with Gradio with our `demo()` mode.

## Learn

To learn more about the LaVague architecture and workflow, head to the [learn section in our docs](../learn/architecture.md)!
