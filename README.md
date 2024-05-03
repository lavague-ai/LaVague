<p align="center">
  <a href="https://github.com/lavague-ai/LaVague/stargazers"><img src="https://img.shields.io/github/stars/lavague-ai/LaVague.svg?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/lavague-ai/LaVague/issues"><img src="https://img.shields.io/github/issues/lavague-ai/LaVague.svg?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/lavague-ai/LaVague/network/members"><img src="https://img.shields.io/github/forks/lavague-ai/LaVague.svg?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/lavague-ai/LaVague/graphs/contributors"><img src="https://img.shields.io/github/contributors/lavague-ai/LaVague.svg?style=for-the-badge" alt="Contributors"></a>
</p>
</br>

<div align="center">
  <img src="static/logo.png" width=140px: alt="LaVague Logo">
  <h1>Welcome to LaVague</h1>

<h4 align="center">
 <a href="https://discord.gg/SDxn9KpqX9" target="_blank">
    <!-- markdown-link-check-disable -->
    <img src="https://dcbadge.vercel.app/api/server/SDxn9KpqX9?compact=true" height='35px' alt="Join our Discord server!">
    <!-- markdown-link-check-enable -->
  </a>
  <a href="https://docs.lavague.ai/en/latest/"><img src="https://img.shields.io/badge/📄-docs-000000?style=for-the-badge&colorA=09c&colorB=555" height='35px' alt="Docs"></a>
</h4>
  <p>The open-source community for Large Action Models</p>
<h1></h1>
</div>

## 🏄‍♀️  What is LaVague?

LaVague is an **open-source Large Action Model framework** for turning **natural language** into **browser actions**.

At LaVague's core, we have an **Action Engine** which uses **advanced AI techniques** (RAG, Few-shot learning, Chain of Thought) to “compile” natural language instructions into browser automation code, by leveraging **Selenium** or **Playwright**.

### LaVague in Action

Here's an example of LaVague being used to execute natural language instructions on a browser to automate web interactions. This example uses the Gradio interface available with the `lavague launch` CLI command:

<div>
  <figure>
    <img src="static/hf_lavague.gif" alt="LaVague Interaction Example" style="margin-right: 20px;">
    <figcaption><b>LaVague interacting with Hugging Face's website.</b></figcaption>
  </figure>
  <br><br>
</div>

## 🚀 Getting Started

### Running LaVague in your local env

You can get started with `LaVague` in 2 steps:

1. Install LaVague & dependencies
```
wget https://raw.githubusercontent.com/lavague-ai/LaVague/main/setup.sh &&
bash setup.sh
```

2. Run your LaVague command!

You can either `launch` an interactive Gradio interface, where you will see both the automation code generated for each instruction but also a live preview of the results of executing the code with a debug tab:
```
lavague launch
```

Or you can use the `build` command to directly get the Python code leveraging Selenium in a file, which you can then inspect & execute locally:
```
lavague build
```

> Note, you'll need an OpenAI API key for this default example and will need the `OPENAI_API_KEY` set in your environment. To use LaVague with a different API, see our [integrations section](https://docs.lavague.ai/en/latest/docs/integrations/home/).

For an end-to-end example of LaVague in a Google Colab, see our [quick-tour notebook](https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb)

## 🎭 Playwright integration

If you want to get started with LaVague build using Playwright as your underlying automation tool, see our [Playwright integration guide](./docs/docs/get-started/playwright.md)

## 🙋 Contributing

We would love your help and support on our quest to build a robust and reliable Large Action Model for web automation.

To avoid having multiple people working on the same things & being unable to merge your work, we have outlined the following contribution process:

1) 📢 We outline tasks on our [`backlog`](https://github.com/orgs/lavague-ai/projects/1/views/3): we recommend you check out issues with the [`help-wanted`](https://github.com/lavague-ai/LaVague/labels/help%20wanted) labels & [`good first issue`](https://github.com/lavague-ai/LaVague/labels/good%20first%20issue) labels
2) 🙋‍♀️ If you are interested in working on one of these tasks, comment on the issue! 
3) 🤝 We will discuss with you and assign you the task with a [`community assigned`](https://github.com/lavague-ai/LaVague/labels/community-assigned) label 
4) 💬 We will then be available to discuss this task with you
5) ⬆️ You should submit your work as a PR
6) ✅ We will review & merge your code or request changes/give feedback

Please check out our [`contributing guide`](./contributing.md) for a more detailed guide.

If you want to ask questions, contribute, or have proposals, please come on our [`Discord`](https://discord.gg/SDxn9KpqX9) to chat!

## 🗺️ Roadmap

TO keep up to date with our project backlog [here](https://github.com/orgs/lavague-ai/projects/1/views/2).

### 🚨 Disclaimer

Note, this project executes LLM-generated code using `exec`. This is not considered a safe practice. We therefore recommend taking extra care when using LaVague (such as running LaVague in a sandboxed environment)!
