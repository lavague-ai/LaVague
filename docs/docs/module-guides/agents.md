# Web Agents

Web Agents wrap around and combine all our key components to allow user to easily automate the actions needed to achieve an objective. Web agents are made up of:

- A [World Model](./world-model.md): Responsible for providing the next natural language instruction needed to eventually reach our objective
- An [Action Engine](./action-engine.md) (and its [driver](./browser-drivers.md)): Responsible for turning instructions into actions and executing them
- Short Term Memory: Provides information about past actions to be considered by the World Model
- An optional [logger](./local-log.md): Logs information about the last agent run
- An optional [TokenCounter](../get-started/token-usage.md): which tracks token usage and estimates cost

![agent-architecture](../../assets/web-agent-architecture.png)

## Web agent arguments

The Web Agent class accepts the following arguments:

Here is the updated table:

| Parameter                | Description                                                                                                                                                                                                                                  | Default Value |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `world_model`            | Required World Model instance                                                                                                                                                                                                               | N/A           |
| `action_engine`          | Required Action Engine instance                                                                                                                                                                                                             | N/A           |
| `n_steps`                | An integer value for the maximum number of steps or instructions you allow your agent to take before reaching a conclusion. Reducing this value can act as a protection against a very costly multi-step query - however, if you set this value too low, your agent may not have enough steps in which to successfully complete the task. | 10            |
| `clean_screenshot_folder`| Boolean value to set whether LaVague should clear all previous files in the "./screenshots" folder before adding new screenshots to this folder.                                                                                              | True          |
| `token_counter`          | An optional TokenCounter object which enables token consumption tracking and price estimation.                                                                                                                                                         | None          |

## Web Agents methods

Let's now take a look at the Agent's key methods and how to use them.

### Get

The `get()` method allows us to set the URL we want our agent to interact with. This method must be used before we start using an Agent with the `run()` or `demo()` methods. 

This method takes a string `url` and navigates to this page with the Action Engine's web driver.

```py
agent.get("https://huggingface.co/docs")
```


If your driver uses `non-headless mode` (set by initializing the driver with the headless=False option), at this point a browser will open and navigate to this page.

If you are in headless mode, the web driver will still navigate to the URL but you won't be able to see this happen in your graphical interface.

### Run

The `Run` method will generate and execute the actions needed to complete an `objective` on your website by leveraging its WorldModel and ActionEngine sub-components.

```py
ret = agent.run("Navigate to the quicktour of PEFT", display=True)
```
It returns a `ActionResultobject` containing: 

- instruction: the user objective
- code: all the code of the successful actions run (for `Navigation Engine` only)
- success: boolean of if the objective was achieved
- output: the output if any (for example information retrieved from a website)

If you are using `non-headless` mode, you will be able to see these actions performed in real-time in your browser window. You can alternatively use the `display` to visualize updated screenshots as the actions are performed if you are using `headless` mode. If not, you will not be able to visualize the navigation taking place in your graphical interface, but will still receive the output of the agent's series of actions.

#### Method arguments:

Here is the updated table including the new options:

| Parameter                | Description                                                                                                                                                                                                                                  | Default Value |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `world_model`            | Required World Model instance                                                                                                                                                                                                               | N/A           |
| `action_engine`          | Required Action Engine instance                                                                                                                                                                                                             | N/A           |
| `n_steps`                | An integer value for the maximum number of steps or instructions you allow your agent to take before reaching a conclusion. Reducing this value can act as a protection against a very costly multi-step query - however, if you set this value too low, your agent may not have enough steps in which to successfully complete the task. | 10            |
| `clean_screenshot_folder`| Boolean value to set whether LaVague should clear all previous files in the "./screenshots" folder before adding new screenshots to this folder.                                                                                              | True          |
| `token_counter`          | A TokenCounter object which enables token consumption tracking and price estimation.                                                                                                                                                         | None          |
| `log_to_db`              | If set to True, logging to local database will be performed allowing users to collect debugging data on their usage. This can also be set with the `LAVAGUE_LOG_TO_DB` environment variable.                                                  | is_flag_true("LAVAGUE_LOG_TO_DB") |
| `step_by_step`           | Enables step-by-step execution of the WebAgent. When set to True, it pauses at each step and enables the user to agree whether to continue or not. This is best used in a Python script where interactive step-by-step control is required.      | False         |

### `Demo`

The demo method works similarly to the `run` method, but will launch an interactive demo mode, which we can access by clicking on the public or local URL generated by the method in your terminal. From there you can input different URLs and objectives and see the steps, actions and outputs in real-time in the built-in browser display and chat box.

```py
agent.demo("Go on the quicktour of PEFT")
```

#### Method arguments:


| Parameter         | Description                                                                                                                                                                                                                                                                                                                                                   | Default |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| objective         | Required argument, a string objective that the web agent should achieve.                                                                                                                                                                                                                                                                                      | N/A     |
| user_data         | User data of any type, but typically structured data such as a JSON or dictionary, to be taken into account by the World Model. For example, you might send an object containing the personal details needed for the Agent to fill in a form. This data is added to the Short Term Memory's current_state with the [`internal_state`][`user_inputs`].             | None    |
| screenshot_ratio  | A float value, by default 1, to adjust the size ratio of the screenshot shown (reducing the size of the screenshots in the visual display could be of interest where screenshots take too long to load). The image width and height is divided by the value you specify. For example, if set to 2, the height and width of the screenshots will be halved in size. | 1       |

### run_step()

This method allows the agent to perform a single step. It is useful for controlled step-by-step debugging. It is ideal for use within a Jupyter notebook environment where you can manually control and observe each step.

You should provide it with your global objective as you would with `run()` or `demo()`.

```py
agent.run_step("Go on the quicktour of PEFT")
```

### display_previous_nodes()

Provides both a visual representation and the HTML code for each element retrieved for the previous step specified.
```py
agent.run("Go on the quicktour of PEFT")
step = 0 # View nodes retrieved for first instruction
agent.display_previous_nodes(step)
```

This is useful for debugging as it allows us to see if the retriever correctly retrieved the relevant web element to perform the instruction.

For example, if the instruction for step 0 was 'click on the 'PEFT' button', you can verify that the button web element was retrieved using this method.

### display_all_nodes()

Similar to the above method, but this will return the nodes retrieved for all steps.