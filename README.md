<p align="center">
  <a href="https://github.com/lavague-ai/LaVague/stargazers"><img src="https://img.shields.io/github/stars/lavague-ai/LaVague.svg?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/lavague-ai/LaVague/issues"><img src="https://img.shields.io/github/issues/lavague-ai/LaVague.svg?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/lavague-ai/LaVague/network/members"><img src="https://img.shields.io/github/forks/lavague-ai/LaVague.svg?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/lavague-ai/LaVague/graphs/contributors"><img src="https://img.shields.io/github/contributors/lavague-ai/LaVague.svg?style=for-the-badge" alt="Contributors"></a>
</p>
</br>

<div align="center">
  <img src="docs/assets/logo.png" width=140px: alt="LaVague Logo">
  <h1>Welcome to LaVague</h1>

<h4 align="center">
 <a href="https://discord.gg/SDxn9KpqX9" target="_blank">
    <img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" height='35px' alt="Join our Discord server!">
  </a>
  <a href="https://docs.lavague.ai/en/latest/"><img src="https://img.shields.io/badge/📄-docs-000000?style=for-the-badge&colorA=09c&colorB=555" height='35px' alt="Docs"></a>
</h4>
  <p>A Large Action Model framework for developing AI Web Agents
</p>
<h1></h1>
</div>

## 🏄‍♀️  What is LaVague?

LaVague is an **open-source Large Action Model framework** to develop AI Web Agents.

Our web agents take an objective, such as "Print installation steps for Hugging Face's Diffusers library" and performs the required actions to achieve this goal by leveraging our two core components:

- A **World Model** that takes an objective and the current state (aka the current web page) and turns that into instructions
- An **Action Engine** which “compiles” these instructions into action code, e.g. **Selenium** or **Playwright** & execute them

## 🚀 Getting Started

### Demo

Here is an example of how LaVague can take multiple steps to achieve the objective of "Go on the quicktour of PEFT":

<p align="center">
  <img src="./docs/assets/demo_agent_hf.gif" alt="Demo for agent">
</p>

### Hands-on 

To do this, the steps are simple:

1. Download LaVague with:

```bash
pip install lavague
```
2. Use our framework to build a Web Agent and implement the objective:

```python
from lavague.retrievers import OpsmSplitRetriever
from lavague.defaults import DefaultEmbedder, DefaultLLM, default_get_selenium_driver
from lavague.action_engine import ActionEngine
from lavague.world_model import GPTWorldModel
from lavague.agents import WebAgent
import requests

driver = default_get_selenium_driver()
action_engine = ActionEngine(DefaultLLM(), OpsmSplitRetriever(DefaultEmbedder(), top_k=3))

examples = requests.get("https://raw.githubusercontent.com/lavague-ai/LaVague/main/examples/knowledge/hf_example.txt").text
world_model = GPTWorldModel(examples=examples)

agent = WebAgent(driver, action_engine, world_model)
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT")
```

For more information on this example and how to use LaVague, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/).

> Note, these examples use our default OpenAI API configuration and you will need to set the OPENAI_API_KEY variable in your local environment with a valid API key for these to work.

For an end-to-end example of LaVague in a Google Colab, see our [quick-tour notebook](https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb)

## 🙋 Contributing

We would love your help and support on our quest to build a robust and reliable Large Action Model for web automation.

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

1) 📢 We outline tasks on our [`backlog`](https://github.com/orgs/lavague-ai/projects/1/views/3): we recommend you check out issues with the [`help-wanted`](https://github.com/lavague-ai/LaVague/labels/help%20wanted) labels & [`good first issue`](https://github.com/lavague-ai/LaVague/labels/good%20first%20issue) labels
2) 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue! 
3) 🤝 We will discuss with you and assign you the task with a [`community assigned`](https://github.com/lavague-ai/LaVague/labels/community-assigned) label 
4) 💬 We will then be available to discuss this task with you
5) ⬆️ You should submit your work as a PR
6) ✅ We will review & merge your code or request changes/give feedback

Please check out our [`contributing guide`](./docs/docs/contributing/contributing.md) for a more detailed guide.

If you want to ask questions, contribute, or have proposals, please come on our [`Discord`](https://discord.gg/SDxn9KpqX9) to chat!

## 🗺️ Roadmap

TO keep up to date with our project backlog [here](https://github.com/orgs/lavague-ai/projects/1/views/2).

### 🚨 Disclaimer

Note, this project executes LLM-generated code using `exec`. This is not considered a safe practice. We therefore recommend taking extra care when using LaVague (such as running LaVague in a sandboxed environment)!

### 📈 Telemetry

By default LaVague records some basic anonymous values to help us gather data to build better agents and Large Action Models:

- Version of LaVague installed
- Code generated for each web action step
- LLM used (i.e GPT4)
- Randomly generated anonymous user ID
- Whether you are using a CLI command or our library directly
- The URL you performed an action on
- Whether the action failed or succeeded
- Error message, where relevant
- The source nodes (chunks of HTML code retrieved from the web page to perform this action)

If you want to turn off telemetry, you can set your `TELEMETRY_VAR` environment variable to `NONE` in your working environment.
