<p align="center">
  <a href="https://github.com/lavague-ai/LaVague/stargazers"><img src="https://img.shields.io/github/stars/lavague-ai/LaVague.svg?style=for-the-badge" alt="Stargazers"></a>
  <a href="https://github.com/lavague-ai/LaVague/issues"><img src="https://img.shields.io/github/issues/lavague-ai/LaVague.svg?style=for-the-badge" alt="Issues"></a>
  <a href="https://github.com/lavague-ai/LaVague/network/members"><img src="https://img.shields.io/github/forks/lavague-ai/LaVague.svg?style=for-the-badge" alt="Forks"></a>
  <a href="https://github.com/lavague-ai/LaVague/graphs/contributors"><img src="https://img.shields.io/github/contributors/lavague-ai/LaVague.svg?style=for-the-badge" alt="Contributors"></a>
</p>
</br>

<div align="center">
  <div>
  <img src="docs/assets/logo.png" width=140px: alt="LaVague Logo">
  <h1>Welcome to LaVague
  </div>
 <a href="https://discord.gg/SDxn9KpqX9" target="_blank">
    <img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" height='35px' alt="Join our Discord server!">
  </a>
  <a href="https://docs.lavague.ai/en/latest/"><img src="https://img.shields.io/badge/📄-docs-000000?style=for-the-badge&colorA=09c&colorB=555" height='35px' alt="Docs"></a>
  </h1>
</div>

## What is LaVague?

LaVague is an AI Web Agent framework that revolutionizes web automation. Our mission is to empower developers to build intelligent, efficient, and reliable web automation solutions with ease.

**Key features:**

- Powerful AI-driven **Web Agents** for effective automation
- An **Agent Studio** web interface to view and replay automated tasks
- **Exporters** to turn agent output into the desired replayable code format for your use cases

**Perfect for:**

- 💻 **Builders**: Automate repetitive tasks and improve workflow efficiency
- 🕵️ **QA Engineers**: Streamline website testing and quality assurance

> ⚠️ **Note: On-premise deployment**
> 
> While LaVague Agents are leveraged via a remote API by default, we can provide on-premise deployment for entreprise users.
>   
> Find out more [here](./docs/get-started/on-prem.md)

## Getting Started

[⌛ GIF GOES HERE]

To use LaVague Web Agents, you'll need to:

1. Get a [LaVague API key]().

2. Set your API key as a `LAVAGUE_API_KEY` in your working environment.

3. Install the LaVague Client:

```bash
pip install lavague
```

You're now ready to start using LaVague Web Agents to perform tasks on the websites of your choice:

```python
from lavague import WebAgent

url = "https://huggingface.co/"
obj = "Return a list of the top 5 trending models on HuggingFace"
agent = WebAgent(api_key="")
ret = agent.run(url=url, objective=obj)

# Print output
print(ret.response)
```

```bash
$ mattshumer/Reflection-Llama-3.1-70B, black-forest-labs/FLUX.1-dev, openbmb/MiniCPM3-4B, deepseek-ai/DeepSeek-V2.5, Qwen/Qwen2-VL-7B-Instruct
```
For more information on how to use LaVague, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/).

## Capabilities

LaVague Agents takes the following inputs:

- A text `objective`
- An **optional** `user_data` dictionary for additional structured data
- A text `url`

They will then:

- Leverage AI to generate and execute a series of actions to complete the `objective` provided.

They output:

- A link to the Agent Studio web interface where you can view and replay the actions performed by LaVague
- Text in the case of information retrieval

They return:

- A trajectory object containing a list of actions that can be converted to various code formats with `exporters`

## Limitations

- **Bot protection**: Some websites may flag LaVague agents as bots and prevent LaVague form performing automated actions 
- **AI-generated code:** LaVague actions are generated with AI - our agents can make mistakes.
- **Web only**: We currently only support automating actions on websites. Automated actions for desktop or specific APIs are planned further along our roadmap.
- **Integrations**: There are a vast number of potential use cases for LaVague and we cannot provide integrations for all potential exports of trajectories. You may need to build your own integrations for specific use cases. 

> We encourage our community to contribute their integrations to our open-source repo. For more information on contributions, see our [contribution guide]().

## Roadmap

The next features we are working on include:

- Local driver integration
- Methods for building reusable Python functions from your LaVague automations
- More QA integrations for a variety of testing frameworks
- An agent hub for sharing use-case specific agent knowledge

## Support

If you're experiencing any issues getting started with LaVague, you can get support via:

- **[GitHub](https://github.com/lavague-ai/LaVague/issues)**: Open a GitHub issue
- **[Discord](https://discord.gg/SDxn9KpqX9)**: Use the `#support` channel to get help from our team
- **[Email](https://www.lavague.ai/contact)**: Fill in our website contact form

## LaVague Legacy

As of September 2024, we have made significant changes to the LaVague project, notably moving the Agent to being fully managed for a more optimized experience.

If you want to use the previous version, you can still access our LaVague Legacy...

- **[GitHub](https://github.com/lavague-ai/LaVague/issues)**: Access the lavague-legacy repo
- **[PyPi]()**: Install the lavague-legacy PyPi package
- **[Docs]()**: Consult the lavague-legacy docs

## Data collection

By default, LaVague collects some telemetry data to help us improve agent performance.

To find a comprehensive list of all data collected by LaVague, see [our Terms of Service]().

To reduce data collection to the minimum collection required to run LaVague which will not be used for improving our agents, set your `LAVAGUE_TELEMETRY` environment variable to `LOW`.

If you want full control over your data flow and to remove the need for an external API, [contact us]() about on-premise deployment.

> ⚠️ **Note: Personal data**
> 
>    Be careful to NEVER include personal information in your objectives or any extra `user_data` sent to Agents.
>    
>    If you send personal information in your objectives/extra `user_data`, it is HIGHLY recommended to set telemetry to `LOW`.
