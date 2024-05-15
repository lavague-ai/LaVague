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
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
```

We will need to set our OpenAI Key as a Colab secret (see the key icon on the left-hand side of the Colab notebook) named 'OPENAI_API_KEY' and then convert it to an environment variable with the same name.

```python
import os

# Check if running in Google Colab
try:
    from google.colab import userdata
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if IN_COLAB:
    os.environ["OPENAI_API_KEY"] = userdata.get('OPENAI_API_KEY')
else:
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
```

We will then build an `ActionEngine`, which is responsible for generating automation code for text instructions and executing them.

By default, our`AcionEngine` will use the following configuration:
- LLM: `OpenAI's gpt-4-1106-preview`
- Embedder: `OpenAI's text-embedding-3-large`
- Retriver: `OPSM retriever`

```python
from lavague.core import ActionEngine

action_engine = ActionEngine(selenium_driver)
```

## World model

Here we will introduce World Models, which are models whose goal is to take a given set of:
- Objective: here the goal to be achieved
- State: here a screenshot of the current page

and outputs an instruction that our `ActionEngine` can turn into Selenium code.

Our current world model uses GPT4 with Vision to output an instruction using a screenshot and a given objective.

We can have a look at the current prompt template [here](https://github.com/lavague-ai/LaVague/blob/main/lavague-core/lavague/core/world_model.py#L77).

Next, we will initialize our WorldModel. To do this, we need to provide the WorldModel with knowledge on how to interact with our chosen website. This knowledge consists of  previous examples for this website of turning observations into instructions, that are then turned into actions.

We can initialize our WorldModel with one of three methods, allowing us to provide this knowledge in different formats:
- `WorldModel.from_hub("URL_SLUG")` : with the `from_hub()` method, we can pull the knowledge from a `.txt` file in the `examples/knowledge` folder of our GitHub repo, which acts as a hub for sharing knowledge files. For our `examples/knowledge/hf_example.txt` file, we provide `hf_example` as input to our `from_hub()` method.
- `WorldModel.from_local("PATH_TO_LOCAL_FILE")`: With the `from_local()` method, you can provide knowledge from a local file.
- `WorldModel("KNOWLEDGE_AS_STRING")`: You can also directly initialize a `WorldModel` with your knowledge as a string.

For the purposes of this demo, we will use the `from_hub()` method.

```python
from lavague.core import WorldModel

world_model = WorldModel.from_hub("hf_example")
```

## Demo

We can now play with it, with a small example where we show our World Model can help achieve a specific goal, here going on the quicktour of Hugging Face's PEFT framework for model finetuning, by providing instructions to our `ActionEngine`:

```python
from lavague.core import WebAgent

agent = WebAgent(action_engine, world_model)
```

```python
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)