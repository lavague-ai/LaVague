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


## Action Engine

**An agent is made up of two key components: an `Action Engine` and a `World Model`.**

Let's start by initializing an `ActionEngine`, which is responsible for generating automation code for text instructions and executing them.

```python
from lavague.core import ActionEngine
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(selenium_driver)
```

!!! tip "Headless vs non-headless"
    We use in this demo non-headless mode, aka you can see you driver being piloted. This is good for debug as you can see your agent live. However, it might not be optimal for performance, as headless requires fewer resources. You can learn more about headless vs non-headless [here](https://www.browserstack.com/guide/what-is-headless-browser-testing).

## World Model

Next, we will initialize our `World Model`, providing it with examples of global objectives for actions and the desired thought process and reasoning we wish it to  replicate to generate the next instruction that needs to be passed to the `ActionEngine`.

```python
from lavague.core import WorldModel

world_model = WorldModel()
```

## Web Agent demo

We can now use these two elements to initialize a `WebAgent` and start playing with it!

In the following example, we show how our agent can achieve a user-defined goal, here going on the quicktour of Hugging Face's PEFT framework for model finetuning.

```python
from lavague.core.agents import WebAgent

agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)

## Recap

Here is the full code to create and run your agent using LaVague:

```python
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine WorldModel
from lavague.core.agents import WebAgent

selenium_driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()

agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

## Learn

To learn more about the LaVague architecture and workflow, head to the [learn section in our docs](../learn/architecture.md)!
