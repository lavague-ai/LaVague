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

### Gradio interface

You can also use LaVague to launch an interactive Gradio interface for using the agent with the `agent.demo()` method.

```py
driver = SeleniumDriver(headless=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()

# Create Web Agent
agent = WebAgent(world_model, action_engine)

# Set URL
agent.get("https://huggingface.co/docs")

# Launch the agent in the Agent Gradio Demo mode
agent.demo("Go on the quicktour of PEFT")
```

You can take a quick look at the `demo` feature in the video below:

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="https://github.com/lavague-ai/LaVague/blob/main/docs/assets/gradio.webm?raw=true" type="video/webm">
  </video>
</figure>

### LaVague Chrome Extension

You can also run LaVague in-browser with our LaVague Chrome Extension:

<iframe width="560" height="315"  src="https://www.youtube.com/embed/f7-pRFtT6hY" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

To learn how to install and get started with the Chrome extension, see our [LaVague extension docs](./docs-chrome.md)

## Key features

### Contexts

By default, we use the OpenAI models defined in our `OpenaiContext` module, found in our `lavague-contexts-openai` package.

We have several other built-in contexts that can be used to set your models to default models from other major AI Providers:

- GeminiContext
- AzureOpenaiContext (part of the lavague-contexts-openai package)
- FireworksContext

To use these, you first need to install the relevant context package:

```bash
pip install lavague-contexts-fireworks
```

> The packages are always named lavague-contexts-[name of context]

Then you can initialize your context and pass it to your ActionEngine and WorldModel using the `from_context()` initialization methods:

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.contexts.fireworks import FireworksContext

# Initialize Context
context = FireworksContext()

selenium_driver = SeleniumDriver()

# Build AE and WM from Context
action_engine = ActionEngine.from_context(context, selenium_driver)
world_model = WorldModel.from_context(context)

agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/")
agent.run("What is this week's top Space of the week?")
```

For more information about our Contexts, see our [customization guide](./customization.md).

### Lavague-tests

We provide a test runner for benchmarking the performance of LaVague.

For more information on how to use our test runner, see our [LaVague testing guide](https://docs.lavague.ai/en/latest/docs/get-started/testing/).

### TokenCounter

We provide tooling to get token usage and cost estimations about your usage of LaVague.

For more information about our TokenCounter, see our [TokenCounter guide](https://docs.lavague.ai/en/latest/docs/get-started/token-usage/).

### Logging

We provide various loggers, allowing you to log information about your LaVague usage to a local file, a local database or to memory.

To log to a local database, you can use the `log_to_db` option when calling the `agent.run` method:

```py
agent.run("Go to the first Model in the Models section", log_to_db=True)
```

For more information about our loggers, see our [logging guide](../module-guides/local-log.md)

### Debugging Tools

We also provide debugging tools, allowing you to enable step-by-step agent execution, run individual agent steps or view the web elements LaVague has sent to the LLM as context for generating the action. You can learn more about these [here](../learn/debug-tools.md)

## Key components explained

### Driver

The Driver component is used to perform actions on web browsers and get information about our current web page.

We currently provide a Selenium Driver component by default, as well as a Playwright Driver option. Feature support varies based on the driver used, learn more in our [Driver documentation](../module-guides/browser-drivers.md).

!!! tip "Avoiding issues around pop ups, CAPTCHA, logins, etc."
    You may experience difficulties using LaVague for logins due to bot protections.

    Here are a couple of tips to avoid these issues when using LaVague:

    ### Manual login

    By creating a driver in non-headless mode, with the option `headless=False`, you can manually log into the website in your driver's browser window after launching it with the `agent.get(URL)` command.

    You can enforce a delay before your program runs the next command by using `time.sleep()` with the `time` package.

    Then you can continue using the session, now logged into your site, with the `agent.run(OBJECTIVE)` commands.

    ### 🍪 Plugging in an existing browser session

    Alternatively, you can use LaVague with your usual browser session to leverage your session's remembered logins. To do this, you need to add the path to your Chrome profile directory as an argument to `user_data_dir` when initializing your browser. 
    
    If not supplied, Chrome starts a fresh session.

For more information on the Driver component see our [Driver module guide](../module-guides/browser-drivers.md)

### Action Engine

Next up, let's consider the Action Engine component. This component receives a natural language text instruction and generates the action needed to carry out this instruction. 

In our example, the Action Engine will perform RAG and generates the code for the action using the default embedding and Large Language Models (OpenAI's text-embedding-3-large & GPT-4o). 

To create an Action Engine with a different `LLM` and `embedding model` you can pass any any `LlamaIndex Embedding` or `LlamaINDEX llm` object` as arguments to your Action Engine, for example:

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq

llm = Groq(model="mixtral-8x7b-32768")

embedding = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

action_engine = ActionEngine(driver=driver, llm=llm, embedding=embedding)
```

To find out more about the Action Engine and how to use custom models see our [Action Engine guide](../module-guides/action-engine.md) or [customization guide](./customization.md).

### World Model

The World Model is responsible for converting the user's global objective into the next instruction for the Action Engine to carry out based on visual and textual information.

The World Model uses a multi-modal model to do this conversion. We use GPT-4o by default, but you can replace the multi-modal LLM with any `LLamaIndex multi-modeal LLM` when initializing your World Model with the following code:

```python
from llama_index.multi_modal_llms.gemini import GeminiMultiModal

mm_llm = GeminiMultiModal(model_name="models/gemini-1.5-pro-latest")

world_model = WorldModel(mm_llm=mm_llm)
```

To find out more about the World Model, see our [World Model guide](../module-guides/world-model.md), and for more information on using custom models, see our [customization guide](./customization.md).

### Web Agent

The Web Agent brings all of these components together and can be used to perform tasks defined by our `objective` argument with the `run` method or to launch an interactive interface with Gradio with our `demo()` mode.

## Learn

To learn more about the LaVague architecture and workflow, head to the [learn section in our docs](../learn/architecture.md)!
