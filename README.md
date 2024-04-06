<p align="center">
  <a href="https://github.com/lavague-ai/LaVague/stargazers"><img src="https://img.shields.io/github/stars/lavague-ai/LaVague.svg?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/lavague-ai/LaVague/issues"><img src="https://img.shields.io/github/issues/lavague-ai/LaVague.svg?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/lavague-ai/LaVague/network/members"><img src="https://img.shields.io/github/forks/lavague-ai/LaVague.svg?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/lavague-ai/LaVague/graphs/contributors"><img src="https://img.shields.io/github/contributors/lavague-ai/LaVague.svg?style=for-the-badge" alt="Contributors"></a>
  <a href="https://github.com/lavague-ai/LaVague/blob/master/LICENSE.md"><img src="https://img.shields.io/github/license/lavague-ai/LaVague.svg?style=for-the-badge" alt="Apache License"></a>
</p>
</br>

<div align="center">
  <img src="static/logo.png" width=140px: alt="LaVague Logo">
  <h1>Welcome to LaVague</h1>

<h4 align="center">
 <a href="https://discord.gg/SDxn9KpqX9" target="_blank">
    <img src="https://img.shields.io/badge/discord-000000?style=for-the-badge&colorB=555" height='35px' alt="Join our Discord server!">
  </a>
  <a href="https://docs.lavague.ai/en/latest/"><img src="https://img.shields.io/badge/docs-000000?style=for-the-badge&colorB=07f" height='35px' alt="Docs"></a>
</h4>
  <p>Copilot for devs to automate automation</p>
<h1></h1>
</div>

## 🏄‍♀️  What is LaVague?

LaVague is an **open-source** project designed to automate automation for devs! 

We use **advanced AI techniques** (RAG, Few-shot learning, Chain of Thought) to turn **natural language instructions** into Python code leveraging **Selenium**. LaVague is designed to make it easy for users to **automate express web workflows** and execute them on a browser.

### LaVague in Action

Here's an examples to show how LaVague can execute natural lanaguge instructions on a browser to automate interactions with a website:

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
sudo bash setup.sh
```

2. Run your LaVague command!

You can either `launch` an interactive demo, where LaVague will execute and show you the results of the automation code it generates for your instruction.
```
lavague-launch --file_path tests/hf.txt --config_file examples/api/openai_api.py
```

Or you can use the `lavague-build` to directly get the Python code leveraging Selenium in a file, which you can then inspect & execute locally.
```
lavague-build --file_path tests/hf.txt --config_file examples/api/openai_api.py
```

For a step-by-step guide or to run LaVague in a Google Colab, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/) which will walk you through how to get set-up and launch LaVague with our CLI tool.

## 🙋 Contributing

We would love your help in making La Vague a reality. 

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

This project executes LLM-generated code using `exec`. This is not considered a safe practice. We therefore recommend taking extra care when using LaVague (such as running LaVague in a sandboxed environment)!
