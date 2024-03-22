# Customization

In the [quick tour](./quick-tour.ipynb), we saw how to use LaVague with our default config file for OpenAI - we also provide default config files for several other [integrations](../integrations/azure-openai.ipynb). In this guide, we will show you how you can modify these config files or create your own for customized use cases.

### Customizable elements

In the configuration file, we can customize the following 5 elements:

- `llm`: The `LlamaIndex` LLM to be used to generate the automation code by the `ActionEngine`
- `embedder`: A `LlamaIndex` embedding model to be used by the `ActionEngine` to 
- `prompt_template`: The prompt template to be used to query the LLM to generate the relevant automation code
- `cleaning_function`: A function used to clean the LLM output to ensure it is code ready to be executed by the `CommandCenter`
- `get_driver`: A `selenium.webdriver` to be used to execute our Selenium automation code

In the `openai.py` default config file, we only provide a new `llm` value, meaning all other values will use our defaults.

![default-openai](../../assets/openai-default.png)

Meanwhile, for our local `DeepSeek Coder` integration, we also provide a custom prompt and cleaning function, required for good performance with this integration.

![default-local](../../assets/local-default.png)

### Using your custom config file

You can go ahead and customize one of our default config files by adding new values for any of these elements within the file, or create your own and then provide it as the `config_path` file when using our CLI tool:

`lavague-launch --file_path hf.txt --config_path custom_file.py`

### Default values

Our default values are:

- `LLM`: HuggingFaceH4/zephyr-7b-gemma-v0.1
- `embedder`: BAAI/bge-small-en-v1.5
- [prompt_template](https://github.com/lavague-ai/LaVague/blob/main/src/lavague/prompts.py)
- [get_driver](https://github.com/lavague-ai/LaVague/blob/cb66a8de9e1210c95ef34df35254ce6875aa69eb/src/lavague/defaults.py#L29)
- [cleaning_function](https://github.com/lavague-ai/LaVague/blob/cb66a8de9e1210c95ef34df35254ce6875aa69eb/src/lavague/action_engine.py#L15)
