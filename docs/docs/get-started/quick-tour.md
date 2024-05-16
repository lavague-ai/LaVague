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

An agent is made up of two components: an `ActionEngine` and a `WorldModel`.

Let's start by initializing an `ActionEngine`, which is responsible for generating automation code for text instructions and executing them.

```python
from lavague.core import ActionEngine
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
```

## World Model

Next, we will initialize our `WorldModel`, providing it with examples of global objectives for actions on this website being broken down into a chain of thoughts and then the next instruction that needs to be passed to the `ActionEngine`.

```python
from lavague.core import WorldModel

world_model = WorldModel.from_hub("hf_example")
```

## Demo

We can now use these two elements to initialize a `WebAgent` and start playing with it!

In the following example, we show how our agent can achieve a user-defined goal, here going on the quicktour of Hugging Face's PEFT framework for model finetuning.

```python
from lavague.core import WebAgent

agent = WebAgent(action_engine, world_model)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)
