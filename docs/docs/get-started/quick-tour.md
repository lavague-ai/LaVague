# Quick Tour

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/LaVague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>

!!! tips "Pre-requisites"

    **Note**: We use OpenAI's models, for the embedding, LLM and Vision model. You will need to set the OPENAI_API_KEY variable in your local environment with a valid API key for this example to work.

    If you don't have an OpenAI API key, please get one [here](https://platform.openai.com/docs/quickstart/developer-quickstart)

## Installation

We start by downloading LaVague.

```bash
pip install lavague
```

Next, we will initialize the default Selenium webdriver, which will be used to execute our actions on the web.

```python
from lavague.defaults import default_get_selenium_driver

driver = default_get_selenium_driver()
```

We will then build an `ActionEngine`, which is responsible for generating automation code for text instructions and executing them.

We will build our `AcionEngine` from the following three key components to do this:
- LLM: `OpenAI's gpt-4-1106-preview`
- Embedder: `OpenAI's text-embedding-3-large`
- Retriever: `OPSM retriever`

```python
from lavague.retrievers import OpsmSplitRetriever
from lavague.defaults import DefaultEmbedder, DefaultLLM
from lavague.action_engine import ActionEngine

llm = DefaultLLM()
embedder = DefaultEmbedder()

retriever = OpsmSplitRetriever(embedder, top_k=3)
action_engine = ActionEngine(llm, retriever)
```

We will finally need to define our `OPENAI_API_KEY`.

```bash
export "OPENAI_API_KEY" = # Your OPENAI_API_KEY
```

## World model

Here we will introduce World Models, which are models whose goal is to take a given set of:
- Objective: here the goal to be achieved
- State: here a screenshot of the current page

and outputs an instruction that our `ActionEngine` can turn into Selenium code.

Our current world model uses GPT4 with Vision to output an instruction using a screenshot and a given objective.

We can have a look at the current prompt template [here](https://github.com/lavague-ai/LaVague/blob/2c0fc2052fd25676da777e3d0de490d9414097b6/src/lavague/prompts.py#L3).

Here we show we can improve our base World Model with knowledge on how to interact with Hugging Face's website by showing previous examples of turning observations into instructions., that are then turned into actions:

```python
from lavague.world_model import GPTWorldModel
import requests

hf_examples = requests.get("https://raw.githubusercontent.com/lavague-ai/LaVague/main/examples/knowledge/hf_example.txt").text
world_model = GPTWorldModel(examples=hf_examples)
```

## Demo

We can now play with it, with a small example where we show our World Model can help achieve a specific goal, here going on the quicktour of Hugging Face's PEFT framework for model finetuning, by providing instructions to our `ActionEngine`:

```python
from lavague.agents import WebAgent

agent = WebAgent(driver, action_engine, world_model)
```

```python
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)