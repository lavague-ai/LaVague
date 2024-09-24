---
description: "An AI Web Agent API for automating web tasks"
---

# LaVague

## What is LaVague?

LaVague is an AI Web Agent framework that revolutionizes web automation. Our mission is to empower developers to build intelligent, efficient, and reliable web automation solutions with ease.

**Key features:**

- Powerful AI-driven **Web Agents** for effective automation
- An **Agent Studio** web interface to view and replay automated tasks
- **Exporters** to turn agent output into the desired replayable code format for your use cases

**Perfect for:**

- 💻 **Builders**: Automate repetitive tasks and improve workflow efficiency
- 🕵️ **QA Engineers**: Streamline website testing and quality assurance

Explore the sections below to get started with LaVague:

<div class="boxes-container">
    <a href="https://docs.lavague.ai/en/drafting-some-docs/docs/get-started/quick-tour/" class="box">
        <h3>Quick start</h3>
        <p>Step-by-step guide on how to use LaVague</p>
    </a>
    <a href="automation" class="box">
        <h3>Automation</h3>
        <p>Explore examples for automating web tasks</p>
    </a>
    <a href="QA" class="box">
        <h3>QA</h3>
        <p>Explore examples for QA use cases</p>
    </a>
</div>

!!! note "On-premise"
    While LaVague Agents are leveraged via a remote API by default, we can provide on-premise deployment for entreprise users.
    
    Find out more [here](./docs/get-started/on-prem.md)

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

![LaVague capabilities light](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/capabilities.png#only-light)
![LaVague capabilities dark](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/capabilities-dark.png#only-dark)

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

!!! info "Community"
    
    We encourage our community to contribute their integrations to our open-source repo.

    For more information on contributions, see our guide [here].


## Roadmap

The next features we are working on include:

- Local driver integration
- Methods for building reusable Python functions from your LaVague automations
- More QA integrations for a variety of testing frameworks
- An agent hub for sharing use-case specific agent knowledge

## Support

If you're experiencing any issues getting started with LaVague, you can:

<div class="boxes-container">
    <a href="https://github.com/lavague-ai/LaVague/issues" class="box">
        <h3>Github</h3>
        <p>Open a GitHub issue</p>
    </a>
    <a href="https://discord.gg/SDxn9KpqX9" class="box">
        <h3>Discord</h3>
        <p>Use the `#support` channel</p>
    </a>
    <a href="https://www.lavague.ai/contact" class="box">
        <h3>Email</h3>
        <p>Fill in our website contact form</p>
    </a>
</div>

## LaVague Legacy

As of September 2024, we have made significant changes to the LaVague project, notably moving the Agent to being fully managed for a more optimized experience.

If you want to use the previous version, you can:

<div class="boxes-container">
    <a href="https://github.com/lavague-ai/LaVague/issues" class="box">
        <h3>Github</h3>
        <p>Access the lavague-legacy repo</p>
    </a>
    <a href="https://discord.gg/SDxn9KpqX9" class="box">
        <h3>PyPi</h3>
        <p>Install the lavague-legacy PyPi package</p>
    </a>
    <a href="https://www.lavague.ai/contact" class="box">
        <h3>Docs</h3>
        <p>Consult the lavague-legacy docs</p>
    </a>
</div>

## Data collection

By default, LaVague collects some telemetry data to help us improve agent performance.

To find a comprehensive list of all data collected by LaVague, see [our Terms of Service]().

To reduce data collection to the minimum collection required to run LaVague which will not be used for improving our agents, set your `LAVAGUE_TELEMETRY` environment variable to `LOW`.

If you want full control over your data flow and to remove the need for an external API, [contact us]() about on-premise deployment.

!!! warning "Personal data" 
    Be careful to NEVER include personal information in your objectives or any extra `user_data` sent to Agents.
    
    If you send personal information in your objectives/extra `user_data`, it is HIGHLY recommended to set telemetry to `LOW`.