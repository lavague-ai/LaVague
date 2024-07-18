# Debug tools

Some simple tools are built-in into LaVague to help you debug agents. Some external tools can also be used. 


## Using Chrome debug tools

You can bind LaVague to a Chrome instance launched in debug mode. This often helps avoiding CAPTCHAs as your session is harder to detect. 

### Launching Chrome in debug

Run these commands in your terminal to launch Chrome in debug mode. 

- Windows: `chrome.exe --remote-debugging-port=9222`
- OSX/: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
- Linux: `google-chrome --remote-debugging-port=9222`

### Attach to the session

Add `chrome_options` to SeleniumDriver to attach to the Chrome debug instance.

```python
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

selenium_driver = SeleniumDriver(headless=False, options=chrome_options)
```


## Run your agent in step by step mode

### `WebAgent(step_by_step=True)`

This parameter is used to enable step-by-step execution of the `WebAgent`. When set to `True`, it prompts the user at each step to continue or not. This is best used in a Python script where interactive step-by-step control is required.

```python
agent = WebAgent(world_model, action_engine, step_by_step=True)
```

## Run one agent step

### `WebAgent.run_step()` 

This method allows the agent to perform a single step. It is useful for controlled step-by-step debugging, making it ideal for use in a Jupyter notebook environment where you can manually control and observe each step.

```python
agent.run_step()
```

## Highlight nodes 
This feature is only supported on Selenium

This method highlights interactive nodes in the specified color (e.g., red). It is useful for visually debugging and identifying interactive elements on a web page.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

selenium_driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(selenium_driver)
agent = WebAgent(world_model, action_engine, step_by_step=True)

agent.get("https://amazon.com/")

# highlight nodes
selenium_driver.highlight_interactive_nodes(color="red")

agent.run_step("Add cat food to my cart")

selenium_driver.highlight_interactive_nodes(color = "blue")


```



You can also remove highlights
```python
selenium_driver.remove_highlight()
```

