# FAQs

## Can I run LaVague with open-source local/remote models?

LaVague's agents use three models:

- a multi-modal model
- the Action Engine's LLM
- the embedding model

Each of these can be replaced with any llama-index compatible alternative with a sufficiently large context window, including open-source ones, with local or remote inference. See our [customization guide](../get-started/customization.md) for more details on how to do this.

!!! warning "Performance"

    While you can try out LaVague with any models that you like, performance varies significantly between models and some models may not perform well enough. We have not currently found an open-source multi-modal LLM able to perform well enough and welcome any support from the community on this!

## How can I disable telemetry?

LaVague collects telemetry by default to help us monitor and improve performance.

If you want to turn off all telemetry, you can set your `TELEMETRY_VAR` environment variable to `"NONE"`.

For more information on how to set environment variables, see the following section.

## How can I set my API keys as environment variables?

When using LaVague, you will need to set any necessary API key environment variables for calls to the:

- Action Engine's LLM
- embedding model
- World Model's multi-modal model

Here, we explain how to set environment variables on Linux, MacOS and Windows.

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