# Action Engine

### What is the Action Engine?

The Action Engine module is responsible for transforming natural lanagueg instructions into code and executing it.

An Action Engine has three sub-engines at its disposal:

- 🚄 Navigation Engine: Generates and executes Selenium code to perform an action on a web page
- 🐍 Python Engine: Generates and executes code for tasks that do not involve navigating or interacting with a web page, such as extracting information
- 🕹️ Navigation Control: Performs frequently required navigation tasks without needing to make any extra LLM calls. So far we cover: scroll up, scroll down & wait

In our agentic workflow, the agent gets the next instruction and the name of the next sub-engine to be used from the WorldModel. This information is then sent to the Action Engine using the `dispatch_instruction` method. 

We can test out this method directly with the Action Engine:

```python
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine

selenium_driver = SeleniumDriver(headless=False, url="https://huggingface.co/")
action_engine = ActionEngine(
    driver=selenium_driver,
)

# Dispatch an instruction to the Navigation Engine
engine_name = "Navigation Engine"
instruction = "Click on the Models button in the top menu"

# Execute the instruction and get the output if applicable
success, output = action_engine.dispatch_instruction(engine_name, instruction)
```

When we call the `dispatch_instruction` method, the following key steps take place: 

- We perform RAG on the web page's source code to get the information needed for our task
- We query the LLM to generate the code needed to perform our action
- We run a cleaning function to ensure we extract code only from our LLM response
- We execute the code
- Information about the Action Engine and code generated are stored with out local logger
- The `dispatch_instruction` method returns:
    - a boolean value letting us know if the action was succesful or not
    - the output of the code, where relevant, such as the result of a knowledge retrieval action using the Python Engine

> Note that the Navigation Control was designed to skip the RAG and LLM steps and pre-defined common navigation methods

### Inspecting the Action Engine with the local logger

In the previous code block, we get the results of the code executed and whether the execution was succesful. But to get more information from our Action Engine, such as viewing the code generated, we need to plug in our `logger` module when running our code.

### Customizing an Action Engine

### Display mode


