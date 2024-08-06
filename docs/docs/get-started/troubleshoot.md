# Troubleshooting common issues

This troubleshooting guide is based on the issues reported back to us from the community and will be updated regularly.

You can use this guide to look for possible solutions if you experience any issues running LaVague.

!!! tip "LaVague latest version"

    One of the most common causes of issues using LaVague is outdated packages. We regularly update and patch our packages.

    If you are having issues with LaVague, please first try running `pip install --upgrade lavague` (or `pip install --upgrade [package_name]` for any other lavague packages).

## Installation issues

If your Python script using LaVague is still returning errors such as `ModuleNotFoundError: No module named 'lavague'` after you have installed our pypi package or you have dependency conflicts in your environment, try running LaVague in a virtual environment.

And even without these issues - installing and using LaVague within a virtual env is good practice.

```py
python -m venv my_env
source my_env/bin/activate
pip install lavague
python test.py
```

## WebDriver exceptions

It is important to note that if you use LaVague with the Driver option `headless=false`, your environment will need to support GUI.

In practice, this means that in environments such as `Google Colab notebooks`, `replit.com` or on VMs without a GUI, you will need to ensure you use `non-headless mode`.

If you have errors in your trace relating back to `selenium.common.exceptions` and `DevToolsActivePort`, this should be due to errors using the Selenium Web Driver in your environment. 

An example of a Selenium error message that could be caused by trying to use `non-headless` mode in an incompatible environment would be:

```sh
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: Chrome failed to start: exited normally.

(session not created: DevToolsActivePort file doesn't exist)
(The process started from chrome location /home/user/.cache/selenium/chrome/linux64/126.0.6478.55/chrome is no longer running, so ChromeDriver is assuming that Chrome has crashed.)
```

By default, our Drivers should run in`headless` mode, but you can verify that this is not overruled by the `headless` option in your code:

| Command                                  | Environment Support        |
|------------------------------------------|----------------------------|
| `driver = SeleniumDriver(headless=True)` | ✅ Supported in all environments |
| `driver = SeleniumDriver()`              | ✅ Supported in all environments |
| `driver = SeleniumDriver(headless=False)`| ❌ GUI environments only        |


!!! tip "Display option"
    When using `headless` mode, you can activate the Agent `display` mode option to display real-time updated screenshots of the agent's progress. This is recommended to provide a visual display when using LaVague in a Google Colab.

    ```py
    agent.run("Print out the name of this week's top trending model", display=True)
    ```

??? note "Running LaVague on Windows Subsystem for Linux 1"

    LaVague may be incompatible with WSL1 due to its compatibility issues with GUI applications.
    
    This can be resolved by [updating to WSL2](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

??? note "Running LaVague with replit.com"

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

    ```py
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

    Make sure to add `lavague` to your dependencies list in your pyproject.toml.
    
    ```code
    [tool.poetry.dependencies]
    python = ">=3.10.0,<3.12"
    lavague = ">=1.1.3"
    ```

## Errors when using LaVague with custom models

While LaVague is compatible with any models supported by LlamaIndex and we encourage you to experiment with different models - some models may not be sufficiently performant with LaVague. This has notably been the case with various open-source models.

You can detect poor performance from the WorldModel's multi-modal LLM by checking the World Model's output in your terminal and verifying that its `thoughts`, `instruction` and `next engine` output seem logical and correct.

If the `LLM` is not performing adequately, you may get the following errors indicating it has failed to generate a supported action:

- ```ValueError(f"Unknown action: {action_name}")```
- ```Exception("Action generation failed. Reason: ", args["value"])``` 

## Getting blocked by CAPTCHAs or pop-ups

Another common source of issues when using LaVague is the Agent's progress getting blocked by CAPTCHAs that it cannot solve.

When we launch LaVague, a new empty browser session will start.

One way to avoid or reduce the likelihood of your Agent facing CATPCHAs, and leverage your existing session settings and cookies, is to plug an existing browser session or instance into LaVague. 

Since the session has already been validated by the website (e.g., through a previous human interaction), it is less likely to trigger CAPTCHAs.

### Using Chrome debug tools

One way you can do this is to bind LaVague to an existing Chrome instance launched in debug mode.

To do this, you will first need to launch Chrome with the `remote-debugging` port option.

- Windows: `chrome.exe --remote-debugging-port=9222`
- OSX/: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
- Linux: `google-chrome --remote-debugging-port=9222`

You can then create and pass `chrome_options` to SeleniumDriver to attach to the debug instance you already launched, which can then be used by LaVague.

```py
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

selenium_driver = SeleniumDriver(headless=False, options=chrome_options)
```

### Plugging in an existing browser session

Another way to plug in an existing browser session is using our Driver's `user_data_dir` option:

```py
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="/home/<YourUsername>/.config/google-chrome")
```

??? tip "User_data_dir path"
    You will need to substitute the path supplied to the `user_data_dir` with the correct path for your browser profile. 
    
    Here are the default paths on Windows, Linux and OSX:

    - **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
    - **Linux**: `/home/<YourUsername>/.config/google-chrome`
    - **OSX**: `/Users/<YourUsername>/Library/Application Support/Google/Chrome`

### Manual interactions for handling CAPTCHAs or pop-ups

A final tip possibility for handling CAPTCHAs or pop-ups is to manually interact with these elements and let LaVague continue its automated navigation after you have resolved the CAPTCHA, pop-up or log-in box that is causing issues. This may be a useful strategy if you're using `LaVague` in non-headless mode and know in advance that there is a certain point at which you will need to manually take an action. 

You can add an `input()` call in your script, which will pause any LaVague execution at a certain point in the code, giving you the time to manually perform whatever action you might need to do on the webpage.

You can then enter any key in the terminal to have your LaVague Agent pick up from this point onwards:

```py
agent.get("https://www.bbc.co.uk")

import time
time.sleep(30)

agent.run("What is the weather in Birmingham")
```

## Truncated output

A final common error is not getting the expected full output from an `objective` like: `give me the top 30 number of products from this page`.

The output might instead list the top 24 number of products, but then get cut off.

One reason for this is that the `max_tokens` of your LLM are not sufficient and need to be increased to get the full output.

You can do this by setting the `max_tokens` option of your LLM to an appropriate amount of tokens.

```py
custom_llm = OpenAI(
    model="gpt-4o",
    max_tokens=1000
)
action_engine = ActionEngine(selenium_driver, llm=custom_llm)
```

To find out more about using custom LLMs, see our [customization guide](./customization.md).

!!! tip "Debugging"

    For a more detailed guide on how to debug and adjust your agent to handle performance errors, see our [debugging guide](../learn/debugging.md).

## Further support

If your issue is not covered here or you need further support, you can ping us on the `#support` channel on [Discord](https://discord.gg/SDxn9KpqX9) or open an [issue](https://github.com/lavague-ai/LaVague/issues) on our GitHub.