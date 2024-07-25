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
- An **Action Engine** which “compiles” these instructions into action code, e.g. **Selenium** or **Playwright** & executes them

## 🚀 Getting Started

### Demo

Here is an example of how LaVague can take multiple steps to achieve the objective of "Go on the quicktour of PEFT":

<p align="center">
  <img src="./docs/assets/demo_agent_hf.gif" alt="Demo for agent">
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

## Key Features

- ✅ [Built-in Contexts](https://docs.lavague.ai/en/latest/docs/get-started/customization/) (aka. configurations)
- ✅ [Customizable configuration](https://docs.lavague.ai/en/latest/docs/get-started/customization/)
- ✅ A [Token Counter](https://docs.lavague.ai/en/latest/docs/get-started/token-usage/) for estimating token usage and costs
- ✅ [Logging tools](https://docs.lavague.ai/en/latest/docs/get-started/customization/)
- ✅ An optional, interactive [Gradio interface](https://docs.lavague.ai/en/latest/docs/get-started/gradio/)
- ✅ [Debugging tools](https://docs.lavague.ai/en/latest/docs/get-started/customization/)

## 🙋 Contributing

We would love your help and support on our quest to build a robust and reliable Large Action Model for web automation.

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

1) 📢 We outline tasks using [`GitHub issues`](https://github.com/lavague-ai/LaVague/issues): we recommend checking out issues with the [`help-wanted`](https:/github.com/lavague-ai/LaVague/labels/help%20wanted) & [`good first issue`](https://github.com/lavague-ai/LaVague/labels/good%20first%20issue) labels
2) 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue! 
3) 🤝 We will discuss with you and assign you the task with a [`community assigned`](https://github.com/lavague-ai/LaVague/labels/community-assigned) label 
4) 💬 We will then be available to discuss this task with you
5) ⬆️ You should submit your work as a PR
6) ✅ We will review & merge your code or request changes/give feedback

Please check out our [`contributing guide`](https://docs.lavague.ai/en/latest/docs/contributing/contributing/) for more details.

## 🗺️ Roadmap

To keep up to date with our project backlog [here](https://github.com/orgs/lavague-ai/projects/1/views/2).

## 💰 How much does it cost to run an agent?

LaVague uses LLMs, (by default OpenAI's `gpt4-o` but this is completely customizable), under the hood.

The cost of these LLM calls depends on: 
- the models chosen to run a given agent
- the complexity of the objective
- the website you're interacting with. 

Please see our [dedicated documentation on token counting and cost estimations](https://docs.lavague.ai/en/latest/docs/get-started/token-usage/) to learn how you can track all tokens and estimate costs for running your agents.

## 📈 Data collection

We want to build a dataset that can be used by the AI community to build better Large Action Models for better Web Agents. You can see our work so far on building community datasets on our [BigAction HuggingFace page](https://huggingface.co/BigAction).

This is why LaVague collects the following user data telemetry by default:

- Version of LaVague installed
- Code generated for each web action step
- LLM used (i.e GPT4)
- Multi modal LLM used (i.e GPT4)
- Randomly generated anonymous user ID
- Whether you are using a CLI command or our library directly
- The instruction used/generated
- The objective used (if you are using the agent)
- The chain of thoughts (if you are using the agent)
- The interaction zone on the page (bounding box)
- The viewport size of your browser
- The URL you performed an action on
- Whether the action failed or succeeded
- Error message, where relevant
- The source nodes (chunks of HTML code retrieved from the web page to perform this action)

### 🚫 Turn off all telemetry

If you want to turn off all telemetry, you should set the `LAVAGUE_TELEMETRY` environment variable to `"NONE"`.

For guidance on how to set your `LAVAGUE_TELEMTRY` environment variable, see our guide [here](https://docs.lavague.ai/en/latest/docs/get-started/FAQs/#how-can-i-set-environment-variables).
