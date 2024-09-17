---
description: "An AI Web Agent API for automating web tasks"
---

# LaVague

LaVague is an AI Web Agent framework to automate web interactions.

It can be used to offload tasks, from testing websites for QA engineers to automating information retrieval, through filling complex forms.

LaVague is made up of:

- The LaVague Agent API - leveraging LLMs to generate and execute multi-action trajectories to perform tasks on the web. 
- A Python SDK including:

    - Methods to faciliate usage of the LaVague API
    - Integrations for specific use cases, such as `exporters` which convert generated actions into `PyTest scripts` for web testing
    - Tooling for users

!!! info "LaVague On-Premise"
        While LaVague Agents are leveraged via a remote API by default. We can provide on-premise deployment of the LaVague for entreprise users.

        Find out more [here](./docs/get-started/on-prem.md)

## Getting Started

To use LaVague Web Agents, you'll need to:

1. Get a [LaVague API key]().

2. Set your API key as a `LAVAGUE_API_KEY` in your working environment.

3. Install the LaVague Client:

```bash
pip install lavague
```

You're now ready to start using LaVague Web Agents to perform tasks on the websites of your choice:

```python
from lavague.core.agents import WebAgent

url = "https://huggingface.co/"
objective = "Return a list of the top 5 trending models on HuggingFace"
agent = WebAgent()
ret = agent.run(url=url, objective=obj)

# Print output
print(ret.response)

# Show screenshot of web page after running LaVague
from PIL import Image
last_action = ret.results[-1:]

img = Image.open(last_result["postaction_screenshot"])
img.show()
```

```bash
$ mattshumer/Reflection-Llama-3.1-70B, black-forest-labs/FLUX.1-dev, openbmb/MiniCPM3-4B, deepseek-ai/DeepSeek-V2.5, Qwen/Qwen2-VL-7B-Instruct
```

![after screenshot](https://raw.githubusercontent.com/lavague-ai/LaVague/draftin-some-docs/docs/assets/after-screenshot.png)

For more information on how to use LaVague, see our [quick-tour](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/).

## Roadmap

The next features we are working on include:

- Streaming option for live visualization of Agent progress
- Local driver integration
- Replay methods so you care store and replay your action trajectories
- Methods to enable you to build replayable functions into your codebase with LaVague
- More QA integrations for a variety of testing frameworks and languages

## Support

If you're experiencing any issues getting started with LaVague, you can:

- Opening a [GitHub issue](https://github.com/lavague-ai/LaVague/issues) describing your issue
- Messaging us in the '#support` channel on our [Discord](https://discord.gg/SDxn9KpqX9") server

## LaVague Legacy

As of the 12/09/2024 we have made significant changes to the LaVague project, including moving a large part of the project to an API.

If you want to access and use the legacy and fully open-source LaVague project , this is still available [here]().

The corresponding PyPi package is available as `lavague-legacy` which you can install by running:

```python
pip install lavague-legacy
```
The corresponding legacy docs can be found [here]().

## Data collection

!!! warning "Personal data" 
    Be careful to NEVER include personal information in your objectives or any extra `user_data` sent to Agents. 
    
    If you send personal information in your objectives/extra `user_data`, it is HIGHLY recommended to turn off all telemetry.

    You can turn off all telemetry by setting the `LAVAGUE_TELEMETRY` environment variable to `"NONE"`.

By default, LaVague collects the following user data to help us to improve our agents:

- A unique user ID
- The URL a task is performed on
- The objective
- Any additional user data sent to agent via `user_data` option
- Date & time of request
- The response of the agent where relevant
- Whether the action fails or succeeds & error message, where relevant
- Version of LaVague used
- The chunks of HTML code retrieved from the web page to perform actions
- Actions generated per Agent step
- Agent's chain of thoughts per step
- The instruction generated & Agent sub-engine used per step
- LLMs used by LaVague API (i.e GPT4), inference times & token consumption
- The interaction zone on the page (bounding box) & viewport size of your browser