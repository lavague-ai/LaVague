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

**An agent is made up of two components: an `Action Engine` and a `World Model`.**

Let's start by initializing an `ActionEngine`, which is responsible for generating automation code for text instructions and executing them.

```python
from lavague.core import ActionEngine
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
```

## World Model

Next, we will initialize our `World Model`, providing it with examples of global objectives for actions and the desired thought process and reasoning we wish it to  replicate to generate the next instruction that needs to be passed to the `ActionEngine`.

```python
from lavague.core import WorldModel

world_model = WorldModel.from_hub("hf_example")
```

## WebAgent Demo

We can now use these two elements to initialize a `WebAgent` and start playing with it!

In the following example, we show how our agent can achieve a user-defined goal, here going on the quicktour of Hugging Face's PEFT framework for model finetuning.

```python
from lavague.core import WebAgent

agent = WebAgent(action_engine, world_model)

agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

![qt_output](../../assets/demo_agent_hf.gif)

## World Model examples file

When we initialized the World Model, we saw that we must provide a file containing examples. This file shows the World Model the desired thought process and reasoning we wish for it to replicate to generate the next instruction.

We initialized the World Model with an example file from our 'hub' - which is an open-source folder in our GitHub repo, which you can find (and contribute to) [here](https://github.com/lavague-ai/LaVague/tree/main/examples/knowledge)!

This was done by using the `WorldModel.from_hub()` method and providing the name of the file we wanted to download, without the file extension ending, i.e. to download `hf_examples.txt`, you should provide `hf_examples` as your argument to this method.

!!! "World Model initialization options"

    Note, as well as pulling an example file from our GitHUb repo with our `from_hub()` method. You can:

    - Specify a path to a local file containing examples by using the `WorldModel.from_local() method`
    - Provide examples directly as a string with the `WorldMethod()` default constructor.

Let's take a look at one of the multiple examples including in that file:

```
Objective: Ask the AI model 'Command R plus' 'What is love'
Thought:
- I am on the Hugging Face website.
- Hugging Face is a company that hosts AI models, and allows users to interact with models on them through the chat.
- Therefore, to answer the objective of asking the AI model 'Command R Plus' 'What is love', we need first to find the model page.
- Given the current screenshot, the fastest way to find the model page seems to be to use the search bar.
Instruction: Type 'Command R plus' on the search bar with placeholder "Search ..." and click on the first result
```
These examples are inserted into our full World Model default prompt:

??? hint "Default World Model prompt in full"

    You are an AI system specialized in high level reasoning. Your goal is to generate instructions for other specialized AIs to perform web actions to reach objectives given by humans.
    Your inputs are an objective in natural language, as well as a screenshot of the current page of the browser.
    Your output are a list of thoughts in bullet points detailing your reasoning, followed by your conclusion on what the next step should be in the form of an instruction.
    You can assume the instruction is used by another AI to generate the action code to select the element to be interacted with and perform the action demanded by the human.

    The instruction should be detailed as possible and only contain the next step. 
    Do not make assumptions about elements you do not see.
    If the objective is already achieved in the screenshot, provide the instruction 'STOP'.

    Here are previous examples:
    ${examples}

    Objective: ${objective}
    Thought:

By providing our `World Model` with examples, we can help our `World Model` to learn to generate instructions by demonstrating the desired thought process and structure for completing tasks.

!!! hint "Contribute to our Knowledge Hub"

    You can contribute example files for a website of your choice, by creating text files with examples of `objectives`, `thoughts` and `instructions` and submitting your file as a `PR` to our GitHub repo.

    See the [contribution section of the docs](../contributing/contributing.md) for more information.

## Learn

To learn more about the LaVague architecture and workflow, head to the [learn section in our docs](../learn/architecture.md)!