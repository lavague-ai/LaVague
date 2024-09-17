# LaVague Architecture & Workflow

![LaVague Workflow](https://raw.githubusercontent.com/lavague-ai/LaVague/draftin-some-docs/docs/assets/architecture-default.png)

## Definitions

Let's first define some key elements in our LaVague Agent architecture:

- `Objective`: The objective is the task the user wants the Web Agent to perform. For example: `"Log into my account and change my username to The WaveHunter."`
- `Action`: A single step needed to move towards achieving the objective, such as `click on the 'username' field`. For security reasons amongst others, we provide a pre-defined list of actions our agents can perform on web elements, such as clicking, entering a text value, etc.
- `Trajectory:` Once the agent has completed its run, it returns a trajectory object to the user which contains information about the run and the list of actions that were executed to reach the final objective. This list of actions could be converted to code and replayed in the future without needing an agent.
- `Driver`: A web driver is leveraged for the execution of the action code and can also provide information to the Agent such as screenshots and HTML code of the reflecting the webpage's latest state. By default, LaVague manages remote drivers for users, but we will also provide a local driver option.

!!! info "More info"
    For a more detailed breakdown of Actions and the Trajectory items. See our [Learn section]().

## Workflow

Let's now take a look at the basic LaVague workflow.

1. We use the `Python client SDK` to send an `objective` and `URL` to the LaVague API.

2. The API will leverage a Web Agent to generate and perform a series of actions needed to achieve this objective. Planning and the generation of actions is performed by LLMs under the hood, while managed or local drivers can be used to perform each action.

3. The agent will return a `Trajectory` JSON object to the user.

4. The user can then optionally use this `Trajectory` object with additional integrations, such as converting the `trajectory` into code or a PyTest script that can be used for web testing.