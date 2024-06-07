---
description: "The open-source Large Action Model framework for AI Web Agents"
---

## 🏄‍♀️  What is LaVague?

LaVague is an **open-source Large Action Model framework** to develop AI Web Agents.

Our web agents take an objective, such as "Print installation steps for Hugging Face's Diffusers library" and performs the required actions to achieve this goal by leveraging our two core components:

- A **World Model** that takes an objective and the current state (aka the current web page) and turns that into instructions
- An **Action Engine** which “compiles” these instructions into action code, e.g. **Selenium** or **Playwright** & execute them

## 🚀 Getting Started

### Demo

Here is an example of how LaVague can take multiple steps to achieve the objective of "Go on the quicktour of PEFT":

<p align="center">
  <img src="https://raw.githubusercontent.com/lavague-ai/LaVague/main/docs/assets/demo_agent_hf.gif" alt="Demo for agent">
</p>

### Hands-on 

You can do this with the following steps:

1. Download LaVague with:

```bash
pip install lavague
```
2. Use our framework to build a Web Agent and implement the objective:

```python
from lavague.core import  WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(selenium_driver)
agent = WebAgent(world_model, action_engine)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")

# Launch Gradio Agent Demo
agent.demo("Go on the quicktour of PEFT")
```

For more information on this example and how to use LaVague, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/).

> Note, these examples use our default OpenAI API configuration and you will need to set the OPENAI_API_KEY variable in your local environment with a valid API key for these to work.

For an end-to-end example of LaVague in a Google Colab, see our [quick-tour notebook](https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb)

## 🙋 Contributing

We would love your help and support on our quest to build a robust and reliable Large Action Model for web automation.

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

1. 📢 We outline tasks on our [`backlog`](https://github.com/orgs/lavague-ai/projects/1/views/3): we recommend you check out issues with the [`help-wanted`](https://github.com/lavague-ai/LaVague/labels/help%20wanted) labels & [`good first issue`](https://github.com/lavague-ai/LaVague/labels/good%20first%20issue) labels

2. 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue! 

3. 🤝 We will discuss with you and assign you the task with a [`community assigned`](https://github.com/lavague-ai/LaVague/labels/community-assigned) label 

4. 💬 We will then be available to discuss this task with you

5. ⬆️ You should submit your work as a PR

6. ✅ We will review & merge your code or request changes/give feedback

Please check out our [`contributing guide`](docs/contributing/contributing.md) for a more detailed guide.

If you want to ask questions, contribute, or have proposals, please come on our [`Discord`](https://discord.gg/SDxn9KpqX9) to chat!

## 🗺️ Roadmap

To keep up to date with our project backlog [here](https://github.com/orgs/lavague-ai/projects/1/views/2).

!!! warning "Security warning"
    Note, this project executes LLM-generated code using `exec`. This is not considered a safe practice. We therefore recommend taking extra care when using LaVague and running LaVague in a sandboxed environment!

## 📈 Data collection

We want to build a dataset that can be used by the AI community to build better Large Action Models for better Web Agents. You can see our work so far on building community datasets on our [BigAction HuggingFace page](https://huggingface.co/BigAction).

This is why LaVague collects the following user data telemetry by default:

- Version of LaVague installed
- Code generated for each web action step
- LLM used (i.e GPT4)
- Randomly generated anonymous user ID
- Whether you are using a CLI command or our library directly
- The URL you performed an action on
- Whether the action failed or succeeded
- Error message, where relevant
- The source nodes (chunks of HTML code retrieved from the web page to perform this action)

### 🚫 Turn off all telemetry

If you want to turn off all telemetry, you can set the TELEMETRY_VAR environment variable to NONE.

If you are running LaVague locally in a Linux environment, you can persistently set this variable for your environment with the following steps:

1) Add TELEMETRY_VAR=NONE to your ~/.bashrc, ~/.bash_profile, or ~/.profile file (which file you have depends on your shell and its configuration)
2) Use `source ~/.bashrc (or .bash_profile or .profile) to apply your modifications without having to log out and back in

In a notebook cell, you can use:

```bash
import os
os.environ['TELEMETRY_VAR'] = "NONE"
```