# Troubleshooting common issues & FAQs

## Pop-ups (log ins, cookies, CAPTCHA, etc.)

A common problem users can have when using LaVague is a failure to get past websites pop-ups such as CAPTCHA, selecting cookies preferences or logging in. While we are working on improving our components abilities to deal with pop-ups, we recommend the following two possible solutions:

### 🍪 Plugging in an existing browser session

When you run LaVague without a `user_data_dir`, a fresh Chrome session is started, with no access to your logins, cookies preferences etc. from your usual browser session.

However you can use LaVague with your usual browser session, which will avoid you needing to log in again or re-submit cookies preferences etc. which can greatly reduce the likelihood of pop-ups disrupting your experience with LaVague.

You can plug in your your usual browser session with the following code:

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="/home/<YourUsername>/.config/google-chrome")
```

!!! hint "Browser profile path"
    You will need to substitute the path supplied to the `user_data_dir` with the correct path for your browser profile. Here are the default paths on Windows, Linux and OSX:

    - **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
    - **Linux**: `/home/<YourUsername>/.config/google-chrome`
    - **OSX**: `/Users/<YourUsername>/Library/Application Support/Google/Chrome`

### Manual interactions for pop-ups

When using a driver in non-headless mode, you can manually take actions on that webpage. Where you know you will need to login to a site or accept cookies for example, you can manually add a pause in your code to allow you time to manually accept cookies or log in:

```python
agent.get("https://www.bbc.co.uk")

import time
time.sleep(5)
time.sleep(5)

agent.run("What is the weather in Birmingham")
```

## WebDriver exceptions

If you have errors in your trace relating back to `selenium.common.exceptions` and `DevToolsActivePort`, this should be due to errors using the Selenium Web Driver in your environment. 

An example of a common Selenium error would be:

```code
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: Chrome failed to start: exited normally.
(session not created: DevToolsActivePort file doesn't exist)
(The process started from chrome location /home/laura/.cache/selenium/chrome/linux64/126.0.6478.55/chrome is no longer running, so ChromeDriver is assuming that Chrome has crashed.)
```

### Environment without GUI support

Ther error show above was caused by running LaVague in non-headless mode in an environment without GUI support.

If you are an environment without GUI support, you will need to ensure your driver is set to `headless` mode with the following code:

```python
driver = SeleniumDriver(headless=True)
```

When using `headless` mode, you can activate a `display` mode to display real-time updated screenshots of the agent's progress. This works well in Google Colab.

```python
agent.run("Print out the name of this week's top trending model", display=True)
```

### Running LaVague with WSL 1 

We are aware that users have been unable to use LaVague in WSL1 - this is due to known compatibility issues with GUI application in WSL1. This should be resolved by [updating to WSL2](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

## Navigation errors

Another common issue you may face is `Navigation errors` like in the following example:

![navigation errors](../../assets/nav-errors.png)

What these errors mean, is that the Navigation Engine did not successfully generate the correct Selenium code needed to interact with the element of the web page needed to achieve its instruction.

There can be several reasons for this and this can often be fixed by modifying options relating to the World Model, Retriever or Action Engine. For a guide on how to debug navigation errors, see our debugging guide (**coming soon**).

## Running LaVague with open-source local and remote models

There has been a lot of interest in using LaVague with open-source models, and even running them locally.

LaVague uses three models (a multi-modal model, the Action Engine's LLM and the embedding model) and each of these can be replaced with any llama-index compatible alternatives with a sufficiently large context window, including open-source ones, with local or remote inference. See our [customization guide](../get-started/customization.md) for more details on how to do this.

!!! warning "Performance"

    While you can try out LaVague with any models that you like, performance varies significantly between models and some models may not perform well enough. We have not currently found an open-source multi-modal LLM able to perform well enough and welcome any support from the community on this!

## How can I turn off telemetry?

LaVague collects the following user data telemetry by default to help us monitor and improve performance:

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

If you want to turn off all telemetry, you can set your `TELEMETRY_VAR` environment variable to `"NONE"`.

For more information on how to set environment variables see the following section!

## How to set environment variables such as API keys

When using LaVague, you will need to set any necessary API keys for calls to the Action Engine's LLM, embedding model and the World Model's multi-modal model in your environment. By default, all these models are provided through the OpenAI API, and so you will need to set your OPENAI_API_KEY in your working environment.

### Linux & MacOS

#### Temporary (session-specific):

- Open a terminal.
- Run the following command to set the variable for the current session:

    ```bash

    export OPENAI_API_KEY="your_api_key_here"
    ```

#### Permanent (across sessions):

- Open your shell's configuration file using a text editor:

    For Bash, Linux users should open the `~/.bashrc` file. MacOS users should open `~/.bash_profile`.

    For Zsh, you should open the `~/.zshrc` file.

- Add the following line at the end of the file:

    ```bash
    export OPENAI_API_KEY="your_api_key_here"
    ```

- Save the file and exit the editor.

- To apply the changes, run:

    ```bash
    source ~/.bashrc   # or source ~/.bash_profile for MacOS users or source ~/.zshrc for Zsh 
    ```

### Windows

#### Temporary (session-specific):

- Open Command Prompt (cmd.exe) or PowerShell.
- Run the following command to set the variable for the current session: `set OPENAI_API_KEY=your_api_key_here`

#### Permanent (across sessions):

- Open Control Panel → System and Security → System → Advanced system settings (on the left).
- In the System Properties window, click on the "Environment Variables..." button.
- Under "User variables" (for your user account), click "New...".
- Set the Variable name to OPENAI_API_KEY and Variable value to your API key.
- Click OK to save the variable.
- Restart any open Command Prompt or PowerShell windows for the change to take effect.

### Verification

To verify that the environment variable is correctly set, you can echo the variable in your terminal or command prompt:

Linux/macOS:

```bash
echo $OPENAI_API_KEY
```

Windows (cmd.exe):

```code
echo %OPENAI_API_KEY%
```

Windows (PowerShell):

```code
echo $env:OPENAI_API_KEY
```

## How much will LaVague usage cost, and how can I minimize the cost?

By default, LaVague leverages the OpenAI API and LLM usage is charged accordingly. The cost of LaVague's LLM usage depends on various factors:

- the models you use
- the complexity of objectives
- the size of the prompt templates used
- the number of `steps` the World Model can take to complete an objective
- how many `retries` the Action Engine may take to achieve each instruction

You can use LaVague with different models including open source ones. See our [customization guide](../get-started/customization.md) for more details.

We recommend you track/limit the cost of your usage with the relevant API provider where relevant.

### Changing cost-related options

There is often a delicate balance to be reached between boosting LaVague's performance (for example by allowing multiple attemps to successfully generate code for an instruction or provide more examples in our prompt templates) and keeping costs low.

We try to make our framework as customizable as possible so you can modify our defaults if they are not right for your use case. 

Here are some relevant elements you can test out adjusting:

### Number of steps

You can limit the number of steps  (and thus potential LLM calls), by default 10, an Agent can take to reach an objective by passing a custom value to the Agent's `n_steps` option:

```python
agent = WebAgent(world_model, action_engine, n_steps=5)
```

However, note if you set this too low, the agent may not be able to successfully achieve your objective.

### Number of retries

You can limit the number of attemps (and thus potential LLM calls), set by default to 5, the Action Engine can take to generate the code for a step by passing a custom value to the Action Engine's `n_attempts` option 

```python
action_engine = ActionEngine(selenium_driver, n_attempts=3)
```

### Modifying prompt templates

You can also view and modify the prompt templates used by the World Model and Navigation Engine (the shorter, the less costly). For more detailed information about the components see our [module guides](../learn/agents.md).
