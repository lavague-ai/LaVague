---
description: "Automate menial tasks with AI with LaVague, generating web automation pipelines from natural language queries"
---

## What is LaVague?

LaVague is an open-source Large Action Model framework designed to automate automation, with a first focus on browser automation. 

LaVague leverages AI to generate web automation pipelines from natural language queries and execute them on a browser. It is built on open-source projects and leverages open-sources models, either locally or remote, to ensure the transparency of the agent and ensures that it is aligned with users' interests.

## Getting started

- See how to get started with LaVague in our [Quick tour](./docs/get-started/quick-tour.ipynb)
- Learn more about LaVague's [architecture](./docs/get-started/architecture.md)
- See how you can [contribute](./docs/contributing/contributing.md) to the project!

## ✨ Features

- **Natural Language Processing**: Understands instructions in natural language to perform browser interactions.
- **Selenium Integration**: Seamlessly integrates with Selenium for automating web browsers.
- **Open-Source**: Built on open-source projects such as transformers and llama-index, and leverages open-source models, either locally or remote, to ensure the transparency of the agent and ensures that it is aligned with users' interests.
- **Local models for privacy and control**: Supports local models like `Gemma-7b` so that users can fully control their AI assistant and have privacy guarantees.
- **Advanced AI techniques**: Uses a local embedding (`bge-small-en-v1.5`) first to perform RAG to extract the most relevant HTML pieces to feed the LLM answering the query, as directly dropping the full HTML code would not fit in context. Then leverages Few-shot learning and Chain of Thought to elicit the most relevant Selenium code to perform the action without having to finetune the LLM (`Nous-Hermes-2-Mixtral-8x7B-DPO`) for code generation.


## 🗺️ Roadmap

This is an early project but could grow to democratize transparent and aligned AI models to undertake actions for the sake of users on the internet.

We see the following key areas to explore:

- Fine-tune local models like a `gemma-7b-it` to be expert in Text2Action
- Improve retrieval to make sure only relevant pieces of code are used for code generation
0 Support other browser engines (playwright) or even other automation frameworks

Keep up to date with our project backlog[ here](https://github.com/orgs/lavague-ai/projects/1/views/2).

## 🙋 Get involved & support

We would love your help in making La Vague a reality.

Please check out our [contributing guide](./docs/contributing//contributing.md) to see how you can get involved!

If you are interested in this project, want to ask questions or need support, please come talk to us on our[ Discord](https://discord.gg/SDxn9KpqX9) server!