---
description: "The open-source community for Large Action Models"
---

## 🏄‍♀️  What is LaVague?

LaVague is an **open-source Large Action Model framework** for turning **natural language** into **browser actions**.

At LaVague's core, we have an **Action Engine** which uses **advanced AI techniques** (RAG, Few-shot learning, Chain of Thought) to “compile” natural language instructions into browser automation code, by leveraging **Selenium** or **Playwright**.

### LaVague in Action

Here's an example of LaVague being used to execute natural language instructions on a browser to automate web interactions. This example uses the Gradio interface available with the `lavague launch` CLI command:

<img src="assets/hf_lavague.gif" alt="LaVague Interaction Example">

## 🚀 Getting Started

### Running LaVague in your local env

You can get started with `LaVague` in 2 steps:

1. Install LaVague & dependencies
```
wget https://raw.githubusercontent.com/lavague-ai/LaVague/main/setup.sh &&
bash setup.sh
```

2. Run your LaVague command!
```
lavague --instructions examples/instructions/huggingface.yaml --config examples/configurations/api/openai_api.py build
```

For a step-by-step guide or to run LaVague in a Google Colab, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/) which will walk you through how to get set-up and launch LaVague with our CLI tool.

## 🎭 Playwright integration

If you want to get started with LaVague build using Playwright as your underlying automation tool, see our [Playwright integration guide](./docs/get-started/playwright.md)

## 🙋 Contributing

We would love your help and support on our quest to build a robust and reliable Large Action Model for web automation.

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

1) 📢 We outline tasks on our [`backlog`](https://github.com/orgs/lavague-ai/projects/1/views/3): we recommend you check out issues with the [`help-wanted`](https://github.com/lavague-ai/LaVague/labels/help%20wanted) labels & [`good first issue`](https://github.com/lavague-ai/LaVague/labels/good%20first%20issue) labels

2) 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue!

3) 🤝 We will discuss with you and assign you the task with a [`community assigned`](https://github.com/lavague-ai/LaVague/labels/community-assigned) label

4) 💬 We will then be available to discuss this task with you

5) ⬆️ You should submit your work as a PR

6) ✅ We will review & merge your code or request changes/give feedback

Please check out our [`contributing guide`](docs/contributing/contributing.md) for a more detailed guide.

If you want to ask questions, contribute, or have proposals, please come on our [`Discord`](https://discord.gg/SDxn9KpqX9) to chat!

## 🗺️ Roadmap

TO keep up to date with our project backlog [here](https://github.com/orgs/lavague-ai/projects/1/views/2).

!!! warning "Disclaimer"

    This project executes LLM-generated code using `exec`. This is not considered a safe practice. We therefore recommend taking extra care when using LaVague (such as running LaVague in a sandboxed environment)!