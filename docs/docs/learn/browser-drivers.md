
# Drivers

Drivers are interfaces for interacting with web browsers autonomously.

Our Driver modules are used to perform actions on web browsers and to get information from our current web page.

We have two Driver options:

- ✅ SeleniumDriver: When the SeleniumDriver is used, our Action Engine will generate and execute code using Selenium
- 🎭 PlaywrightDriver: When the PlaywrightDriver is used, our Action Engine will generate and execute code using Playwright

## Selenium Driver

The Selenium Driver is installed by default when you install `lavague`.

You then need to initialize the Driver and pass it to your Action Engine with the following code:

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
```

You can then carry on using LaVague to perform tasks with our Web Agents.

```bash
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent

world_model = WorldModel()
agent = WebAgent(WorldModel(), action_engine)
agent.get("https://huggingface.co/docs")
result = agent.run("Go on the quicktour of PEFT")
```

## Playwright driver

If you prefer to use our Playwright driver, you will first need to install the Playwright driver package:

```bash
pip install lavague.drivers.playwright
```

Then you can initialize your PlaywrightDriver and pass it to the Action Engine with the following code:

```bash
from lavague.drivers.playwright import PlaywrightDriver

playwright_driver = PlaywrightDriver()
action_engine = ActionEngine(playwright_driver)
```

You can then use LaVague as usual (see the final example of the Selenium Driver section).

!!! note "Playwright Driver limitations"
    The Playwright Driver is not compatible with:

        - running LaVague in Google Colabs/notebooks
        - with the Gradio demo launched via the `agent.demo()` method
        
    This is due to compatibility issues with the Playwright async API. 

    > If you want us to work on implementing a fix by supporting the Playwright sync API, please open a feature request on GitHub so we can gauge interest.

## Optional arguments

You can see all optional driver options here:

??? note "Optional driver options"

    | Parameter                  | Description                                                                                                                                                  |
    |----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | url                        | A string argument which can be used to pass a URL directly to the driver, instead of providing it via the Agent                                              |
    | get_sync_playwright_page (**playwright only**)  | This function can be used to overwrite the init function of Playwright driver to implement a custom init function, accepting custom driver options, for example |
    | get_selenium_driver (**Selenium only**)       | This function can be used to overwrite the init function of Selenium driver to implement a custom init function, accepting custom driver options, for example |
    | headless                   | Boolean value to set headless or non-headless mode                                                                                                            |
    | width                      | Integer value for width of the driver's browser window in pixels                                                                                              |
    | height                     | Integer value for height of the driver's browser window in pixels                                                                                             |
    | user_data_dir              | Path to your Chrome profile directory. If left empty, Chrome starts a fresh session every time. If provided, Chrome starts with your profile's settings and data, this can help avoid bot protections |
    no_load_strategy (**Selenium only**) | If True, Selenium's default load strategy, which waits for the page to be fully loaded before returning, is deactivated. This option should be set to True when using our `agent.demo()` method to avoid slowdown. Instead, LaVague will handle detecting when the page is fully loaded when using this method. However, this option is not recommended with the `agent.run()` method however. |

### Plugging in an existing browser session

By default, the driver starts with a blank user session. But you can change these settings with the following arguments:

### Headless vs non-headless mode

By default, the drivers will start with a headless session. This means, it will not open a browser on your machine where you can watch in real-time the actions the driver is performing. This can be useful when running LaVague in an environment where you don't have access to the browser.

You can change to non-headless mode by initializing your driver with the `headless=False` argument: 
```python
driver = SeleniumDriver(headless=False)
```

> When using `headless` mode, you can activate a `display` mode to display real-time updated screenshots of the agent's progress: `agent.run`: `agent.run("Print out the name of this week's top trending model", display=True)`. This can be useful when testing LaVague in an environment like `Google Colab`, for example.

### Plugging in an existing browser session

By using the Driver's `user_data_dir` argument, you can leverage your default browser settings, cookies, etc. This can remove the need to log in on sites you are already logged in with, which can avoid running into issues with bot protections in log in interactions.

To use your existing Chrome profile, you need to locate the profile path on your operating system. Here are the default locations for Windows, Linux, and OSX:

- **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
- **Linux**: `/home/<YourUsername>/.config/google-chrome`
- **OSX**: `/Users/<YourUsername>/Library/Application Support/Google/Chrome`

You can then pass this path via the `user_data_dir` argument.

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data")
```