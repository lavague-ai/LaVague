# Debug tools

This page provides an overview of the basic built-in debugging tools we provide and a full example setup. 


## Using Chrome debug tools

You can bind LaVague to an existing Chrome instance launched in debug mode. This can help avoiding CAPTCHAs and allows you to leverage your session settings and passwords. 

### Launching Chrome in debug

Run these commands in your terminal to launch Chrome in debug mode. 

- Windows: `chrome.exe --remote-debugging-port=9222`
- OSX/: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
- Linux: `google-chrome --remote-debugging-port=9222`

### Attach to the session

Create and pass `chrome_options` to SeleniumDriver to attach to the debug instance you already launched. 

```py
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

selenium_driver = SeleniumDriver(headless=False, options=chrome_options)
```

## Run your agent in step by step mode

The `step_by_step` option can be set when using the `agent.run()` method to enable step-by-step execution of the `WebAgent`.

When set to `True`, it pauses at each step and enables the user to agree whether to continue or not. This is best used in a Python script where interactive step-by-step control is required.

```py
agent = WebAgent(world_model, action_engine) 
agent.run(objective=obj, step_by_step=True)
```

## Run one agent step

This method allows the agent to perform a single step. It is useful for controlled step-by-step debugging. It is ideal for use within a Jupyter notebook environment where you can manually control and observe each step.

```py
agent.run_step(objective)
```

## Highlight nodes 

This SeleniumDriver method highlights interactive nodes in the specified color (e.g., red). 

It is useful for visually debugging and identifying interactive elements on a web page.

```py
selenium_driver.remove_highlight()
selenium_driver.highlight_interactive_nodes(color="blue")
```

## Example debug setup

We will bind to a Chrome debug session and run the agent manually while highlighting interactable elements at each step. 

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from selenium.webdriver.chrome.options import Options

# add debug port to chrome options
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# include chrome options 
selenium_driver = SeleniumDriver(options=chrome_options)

world_model = WorldModel()
action_engine = ActionEngine(selenium_driver)

# create the agent, don't run it
agent = WebAgent(world_model, action_engine)

# prepare for the run and load the URL
objective = "Add cat food to my cart"
agent.prepare_run()
agent.get("https://amazon.com/")

# highlight nodes in red
selenium_driver.highlight_interactive_nodes(color="red")

# run one step and highlight nodes in blue
agent.run_step(objective)
selenium_driver.highlight_interactive_nodes(color = "blue")

# run another step and highlight nodes in green
agent.run_step(objective)
selenium_driver.highlight_interactive_nodes(color = "green")
```
