# Troubleshooting common issues & FAQs

## Popups (logins, cookies, CAPTCHA, etc.)

A common problem users can have when using LaVague is a failure to get past website pop-ups such as CAPTCHA, accepting cookies or logging in. While we are working on improving our agents' abilities to deal with pop-ups, we recommend the following two possible solutions:

#### 🍪 Plugging in an existing browser session

When you run LaVague without a `user_data_dir`, a blank Chrome session is started, with no access to your usual logins, cookies preferences, etc.

However, you can change this and plug in your usual browser session with the following code:

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="/home/<YourUsername>/.config/google-chrome")
```

This will avoid you needing to log in again or re-submit cookies preferences etc. on sites you already use, which can greatly reduce the likelihood of popups causing issues when using LaVague.

??? hint "User_data_dir path"
    You will need to substitute the path supplied to the `user_data_dir` with the correct path for your browser profile. 
    
    Here are the default paths on Windows, Linux and OSX:

    - **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
    - **Linux**: `/home/<YourUsername>/.config/google-chrome`
    - **OSX**: `/Users/<YourUsername>/Library/Application Support/Google/Chrome`

#### Manual interactions for pop-ups

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
(The process started from chrome location /home/user/.cache/selenium/chrome/linux64/126.0.6478.55/chrome is no longer running, so ChromeDriver is assuming that Chrome has crashed.)
```

#### Environment without GUI support

The error above was caused by running LaVague in non-headless mode in an environment without GUI support.

If you are using an environment without GUI support, you will need to ensure your driver is set to `headless` mode with the following code:

```python
driver = SeleniumDriver(headless=True)
```

When using `headless` mode, you can activate a `display` mode to display real-time updated screenshots of the agent's progress. This works well in Google Colab.

```python
agent.run("Print out the name of this week's top trending model", display=True)
```

??? note "Running LaVague on Windows Subsystem for Linux 1"

    LaVague may be incompatible with WSL1 due to its compatibility issues with GUI applications.
    
    This can be resolved by [updating to WSL2](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

??? note "Running Lavgue with replit.com"

    To get LaVague working in a `replit.com` environment, you will need to add the following packages to the replit.nix file:

    ```code
    {pkgs}: {
    deps = [
        pkgs.geckodriver
            pkgs.python38Full
            pkgs.chromium
            pkgs.chromedriver
    ];
    }
    ```

    > To access the replit.nix file, you'll need to click on `show hidden files`.

    Then you can use LaVague with the Selenium Driver set to headless mode.

    ```python
    from lavague.core import  WorldModel, ActionEngine
    from lavague.core.agents import WebAgent
    from lavague.drivers.selenium import SeleniumDriver
    import os
    my_secret = os.environ['OPENAI_API_KEY']
    selenium_driver = SeleniumDriver(headless=True)
    world_model = WorldModel()
    action_engine = ActionEngine(selenium_driver)
    agent = WebAgent(world_model, action_engine)
    agent.get("https://huggingface.co/docs")
    ret = agent.run("What is the top model?")
    print(ret.output)
    ```

    Make sure to add `lavague` to your depencies list in your pyproject.toml.
    
    ```code
    [tool.poetry.dependencies]
    python = ">=3.10.0,<3.12"
    lavague = ">=1.1.3"
    ```
    
## Navigation errors

Another common issue some users face is `Navigation errors`:

![navigation errors](../../assets/nav-errors.png)

These errors mean that the Navigation Engine did not successfully generate the correct Selenium code needed to interact with the element of the web page needed to achieve its instruction.

There can be several reasons for this and this can often be fixed by modifying options relating to the World Model, Retriever or Action Engine. For a guide on how to debug navigation errors, see our debugging guide (**coming soon**).

## Can I run LaVague with open-source local/remote models?

LaVague's agents use three models:

- a multi-modal model
- the Action Engine's LLM
- the embedding model

Each of these can be replaced with any llama-index compatible alternative with a sufficiently large context window, including open-source ones, with local or remote inference. See our [customization guide](../get-started/customization.md) for more details on how to do this.

!!! warning "Performance"

    While you can try out LaVague with any models that you like, performance varies significantly between models and some models may not perform well enough. We have not currently found an open-source multi-modal LLM able to perform well enough and welcome any support from the community on this!

## How can I turn off telemetry?

LaVague collects telemetry by default to help us monitor and improve performance.

If you want to turn off all telemetry, you can set your `TELEMETRY_VAR` environment variable to `"NONE"`.

For more information on how to set environment variables, see the following section.

## How to set environment variables such as API keys

When using LaVague, you will need to set any necessary API key environment variables for calls to the Action Engine's LLM, embedding model and the World Model's multi-modal model.

Below, we explain how to set environment variables on Linux, MacOS and Windows.

### Linux & MacOS

#### Temporary (session-specific):

Run the following command to set the variable for the current session:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

#### Permanent (across sessions):

- Open your shell's configuration file using a text editor:

    For Bash, Linux users should open the `~/.bashrc` file. MacOS users should open `~/.bash_profile`.

    For Zsh, you should open the `~/.zshrc` file.

- Add the following line at the end of the file and save the file:

    ```bash
    export OPENAI_API_KEY="your_api_key_here"
    ```

- To apply the changes straight away, run:

    ```bash
    source ~/.bashrc # or source ~/.bash_profile for MacOS users or source ~/.zshrc for Zsh 
    ```

You verify that the environment variable is correctly set by printing out the variable in your terminal:

```bash
echo $OPENAI_API_KEY
```

??? "Setting environment variables on Windows"

    #### Temporary (session-specific):

    Run the following command to set the variable for the current session: `set OPENAI_API_KEY=your_api_key_here`

    #### Permanent (across sessions):

    - Open Control Panel → System and Security → System → Advanced system settings (on the left).
    - In the System Properties window, click on the "Environment Variables..." button.
    - Under "User variables" (for your user account), click "New...".
    - Set the Variable name to OPENAI_API_KEY and Variable value to your API key.
    - Restart any open Command Prompt or PowerShell windows for the change to take effect.

    ### Verification

    To verify that the environment variable is correctly set, you can echo the variable in your command prompt:

    Windows (cmd.exe):
    ```code
    echo %OPENAI_API_KEY%
    ```

    Windows (PowerShell):
    ```code
    echo $env:OPENAI_API_KEY
    ```

## How much will LaVague usage cost?

By default, LaVague leverages the OpenAI API and LLM usage is charged accordingly. The cost of LaVague's LLM usage depends on various factors:

- the models you use
- the complexity of objectives
- the size of the prompt templates used
- the number of `steps` the World Model can take to complete an objective
- how many `retries` the Action Engine may take to achieve each instruction

You can use LaVague with different models including open source ones. See our [customization guide](../get-started/customization.md) for more details.

We recommend you track/limit the cost of your usage with the relevant API provider.

??? "Custom options to reduce token usage"

    There is a balance to be reached between boosting LaVague's performance (for example by allowing multiple attempts to successfully generate code for an instruction or provide more examples in our prompt templates) and keeping cost relatively low.

    We aim to make our framework as customizable as possible so you can modify our defaults if they are not right for your use case. 

    Here are some cost-related elements you can adjust:

    ### Number of steps

    You can limit the number of steps  (and thus potential LLM calls), by default 10, an Agent can take to reach an objective by passing a custom value to the Agent's `n_steps` option:

    ```python
    agent = WebAgent(world_model, action_engine, n_steps=5)
    ```

    However, note if you set this too low, the agent may not be able to successfully achieve your objective.

    ### Number of retries

    You can limit the number of attempts (and thus potential LLM calls), set by default to 5, the Action Engine can take to generate the code for a step by passing a custom value to the Action Engine's `n_attempts` option 

    ```python
    action_engine = ActionEngine(selenium_driver, n_attempts=3)
    ```

    ### Modifying prompt templates

    You can also view and modify the prompt templates used by the World Model and Navigation Engine (the shorter, the less costly). For more detailed information about the components see our [module guides](../learn/world-model.md).