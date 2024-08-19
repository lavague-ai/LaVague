
# Drivers

Drivers are interfaces for interacting with web browsers autonomously.

Our Driver modules are used to perform actions on web browsers and to get information from our current web page.

We have three Driver options:

- ✅ SeleniumDriver: the Action Engine will generate and execute code using Selenium. We use the SeleniumDriver by default and it has the most complete feature set. 
- 🎭 PlaywrightDriver: the Action Engine will generate and execute code using Playwright
- 🖥️ Chrome extension: when used along the DriverServer to generate code, the Chrome extension will execute JavaScript

## Driver feature support

Not all agent features are supported by all drivers. **Selenium is our preferred option** since it currently supports the widest range of features. We welcome community contributions to help us increase support coverage for different drivers.


| Feature                  | Selenium  | Playwright       | Chrome Extension                     |
|--------------------------|-----------|------------------|--------------------------------------|
| Headless agents    | ✅ | ⏳ | N/A |
| Handle iframes     | ✅ | ✅ | ❌ |
| Open several tabs  | ✅ | ⏳ | ✅  |
| Highlight elements | ✅ | ✅  | ✅ |
| Remote driver (Browserbase) | ✅ | ❌ | ❌ |


✅ supported  
⏳ coming soon  
❌ not supported 

## Selenium Driver

The Selenium Driver is installed by default when you install `lavague`.

You then need to initialize the Driver and pass it to your Action Engine with the following code:

```py
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

### Plugging in an existing browser session

By default, the driver starts with a blank user session. But you can change these settings with the following arguments:

### Headless vs non-headless mode

By default, the drivers will start with a headless session. This means, it will not open a browser on your machine where you can watch in real-time the actions the driver is performing. This can be useful when running LaVague in an environment where you don't have access to the browser.

You can change to non-headless mode by initializing your driver with the `headless=False` argument: 
```py
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

```py
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data")
```

### Using a remote driver (Browserbase)

The `SeleniumDriver` supports running remote drivers using Browserbase.

1. Create an account on [Browserbase](https://www.browserbase.com/)
2. Get your `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`. You can optionally set them as environment variables.
3. Create a remote driver

```py
from lavague.drivers.selenium import SeleniumDriver
from lavague.drivers.selenium import BrowserbaseRemoteConnection

browserbase_connection = BrowserbaseRemoteConnection('http://connect.browserbase.com/webdriver', api_key = "your_key", project_id="your_project_id")
```

4. Create and run an agent

```py
with SeleniumDriver(remote_connection=browserbase_connection) as selenium_driver:
    world_model = WorldModel()
    action_engine = ActionEngine(selenium_driver)
    agent = WebAgent(world_model, action_engine)
    agent.get("https://wikipedia.org")
    agent.run("Search for AI")
``` 