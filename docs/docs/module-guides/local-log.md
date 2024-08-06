# Agent Logger

### What is the Agent Logger?

When you use `agent.run()`, the `AgentLogger` captures information about the last agentic run. 

Logs can be retrieved and viewed in **several formats**:

- as a pandas DataFrame
- logged locally to a `.txt` file
- logged to a SQLite database

You can view the columns of information added to the log per step in the agentic run attempted here:

??? note "Logger columns"

    | Column Name                   | Description                                                                                                     |
    |------------------------------|-----------------------------------------------------------------------------------------------------------------|
    | `current_state:`             | Contains information about the external or internal observations the World Model used for this step              |
    | `past`                       | History of instructions sent to the Action Engine by the World Model and whether they succeeded or failed       |
    | `world_model_prompt`         | The prompt sent to the World Model to generate the next instruction for the Action Engine needed to achieve the global objective |
    | `world_model_output`         | The reasoning of the World Model, the engine it selected to carry out the next instruction, and the instruction itself |
    | `world_model_inference_time` | Time taken for World Model inference                                                                            |
    | `engine_log`                 | Contains logs related to the specific Action Engine sub-engine used                                            |
    | `success`                    | Whether the step was successful or not in achieving the objective                                              |
    | `output`                     | Output of the step, if relevant (for example, information scraped from a web page)                              |
    | `code`                       | The code generated for this step                                                                                |
    | `html`                       | The code retrieved from the web page and sent as context for the action                                          |
    | `screenshots_path`           | The path where your screenshots are stored locally                                                             |
    | `url`                        | The URL on which the action was run                                                                             |
    | `date`                       | The date and time at which the action was run                                                                   |
    | `run_id`                     | The unique ID for the agent run                                                                                 |
    | `step`                       | An integer representing which step this row refers to in a multi-step pipeline                                   |
    | `screenshots`                | All screenshots taken during the run                                                                            |
    | `engine`                | The names of engines used for each step                                                                            |
    | `engine`                | The instructions produced for each step                                                                            |
    | `tab_info`                | The currently opened tabs and which one is in focus                                                                          |

## Examples

### Logging to a pandas DataFrame

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/module-guides/notebooks/logger.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open code examples in Colab"></a>


Run your agent as usual, and then retrieve the logs DataFrame with `agent.logging.return_pandas()`. This is best suited for usage in a Jupyter notebook. 

```python
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

selenium_driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()

agent = WebAgent(world_model, action_engine)

agent.get("https://huggingface.co/")
agent.run("What is the first model in the Models section?")

# Retrieve pandas DataFrame with logs
df_logs = agent.logger.return_pandas()
```

Now, let's look at the code for the last step ran from within our log DataFrame:
```python
# Pandas option to ensure we show all text in column
import pandas as pd
pd.set_option('display.max_colwidth', None)

# Print the code generated for step 0 of our run
step = 0
print(df_logs['code'][step])
```

This provides us with the following code.
![code](../../assets/code.png)

Next, we can display the first screenshot taken for the first step with the following code:

```python
from IPython.display import display

step = 0
image = 0
display(df_logs["screenshots"][step][image])
```
This will display the following image.
![screenshot](../../assets/screenshot-2.png)

Finally, let's take a look at the World model's reasoning for the first step:

```python
# Print the World Model thoughts generated for step 0 of our run
step = 0
print(df_logs.at[step, 'world_model_output'])
```

This gives us the following output.
![code](../../assets/thoughts.png)

Next let's look at the nodes, or HTML components, collected by our retriever for our task.

The nodes sent to our Navigation Engine's LLM for each attempt to generate code for an action are stored in the `engine_log` column of our log.

> Note, due to an on-going migration from a legacy feature, when accessing the engine log, we still need to index into 0 to access data relating to the first instruction - as previously instructions could be split into multiple parts.

```python
# Print the code generated for step 0 of our run
attempt = 0
from IPython.display import display, HTML, Code

x = 0

# sub instruction index - to be removed in the future 
sub_instruction = 0
for node in df_logs.at[attempt, 'engine_log'][sub_instruction]['retrieved_html']:
    print(f"node {x}")
    x = x + 1
    display(HTML(node)) # Display node as visual element
    display(Code(node, language="html")) # Display code
```

This gives us an output as follows:

If you are using the logs to debug and find that the nodes do not show the relevant HTML components to complete the instruction, we know that the task has failed because of the performance of the `Retriever`.

### Exporting logs to a local file

If you want your logs to be saved to a local file. You can create a `LocalLogger` object with the path of your logger file, or the file you wish LaVague to create:

```python
from lavague.core.logger import LocalLogger
log = LocalLogger(log_file_path="log.txt")
```

When initializing your Web Agent, you'll need to pass it your Local Logger with the `logger` argument:

```python
agent = WebAgent(world_model, action_engine, logger=log)
```

After using the agent, your logs will now be stored in the file you specified.

> If you don't appear to have the `LocalLogger` in your current version of LaVague, you can upgrade lavague-core with" `pip install --upgrade lavague-core`

### Logging to SQLite

LaVague also supports logging directly to a SQLite database when running your agent. This feature provides a structured way to store and query your agent's logs. 

Here's how to use it:

1. First, ensure you have SQLite installed on your system. If not, you can typically install it using your system's package manager or download it from the [official SQLite website](https://www.sqlite.org/download.html).

2. When running your agent, add the `log_to_db=True` parameter to the `run()` method:

```py
agent.run("Go to the first Model in the Models section", log_to_db=True)
```

This will automatically create (if it doesn't already exist in your current environment) or add to a SQLite database file named `lavague_logs.db` in your current working directory and log all the agent's actions to it.

- The database will contain a table named "Logs" with columns corresponding to the various aspects of the agent's operations.

- You can then use SQLite to query and analyze your logs.

This feature allows for more persistent logging, which can be especially useful for debugging and tracking the performance of your LaVague agents over time.

## Advanced: Manually logging sub-components

The logger runs automatically whenever you use the `agent.run()` method and is accessible via `agent.logger`. 

However, if you are using an `Action Engine`, `Navigation Engine`, `Navigation Control`, `Python Engine` or `World Model` directly, rather than via our `Agent` wrapper, you can directly instantiate and use our `AgentLogger` class directly with them to manage the logging of these components.

Below, we take a look at an example of how we can do this by with the Action Engine.

??? tip "Advanced example"

    Firstly, let's create out Action Engine and instance of AgentLogger:

    ```py
    from lavague.drivers.selenium import SeleniumDriver
    from lavague.core.logger import AgentLogger
    from lavague.core import ActionEngine

    selenium_driver = SeleniumDriver(headless=True, url="https://huggingface.co/")
    action_engine = ActionEngine(
        driver=selenium_driver,
    )

    # Initialize your logger
    logger = AgentLogger()
    ```

    Next, we can start a new logger run and add our logger to our Action Engine sub-component. We will also need to collect observations from the driver as this must be added to each logger run.

    ```py
    # Start a new logging run
    logger.new_run()

    # Add logging to NavigationEngine
    action_engine.navigation_engine.set_logger(logger)

    obs = selenium_driver.get_obs()
    ```

    Now we will execute an action, add the required observations to the logger and signal to that we have finished our action with the `end_step()` method. We can then get a DataFrame with the logs for this action.

    ```py
    # Engine & instruction
    engine_name = "Navigation Engine"
    instruction = "Show me the top model"

    # Execute the instruction
    ret = action_engine.dispatch_instruction(engine_name, instruction)

    # Add required driver info to logs and end the logging step
    logger.add_log(obs)
    logger.end_step()

    # Retrieve and print logs as a pandas DataFrame
    df_logs = logger.return_pandas()
    ```