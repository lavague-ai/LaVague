# Playwright Integration

In this guide, we're going to show you how you can get started with 'lavague build' with Playwright.

🔨`lavague build` will take your text instructions and leverage a large action model to create a Python file with the automation code needed to perform that action.

!!! note "Playright vs Selenium"

    - 🚀 Playwright is faster with better performance than Selenium.
    - ⚡ Unlike Selenium, it doesn't require any additional driver installations as cross-browser support is built-in.
    - ⏳ However, we currently only support Playwright for the `lavague build` command, due to constraints around supporting an async library with `launch` and the vscode extension.

|         | Playwright | Selenium |
| :---:          | :---: | :---: |
lavague build    | ✅  | ✅ |
lavague launch   | ❌ | ✅ | 
VSCode extension | ❌ | ✅ | 

## Getting started with Playwright

To get started with `lavague build` with Playwright, you need to:

**Step one:** Download lavague with the optional Playwright dependencies

```
pip install lavague[playwright]
```

**Step two:** Run your lavague build command with a `Playwright` configuration file

For example, you can run lavague build with our example Playright configuration file and instructions file with the following command from the root of our LaVague repo:

`lavague -c examples/configurations/api/openai_api_playwright.py -i examples/instructions/hugginface.yaml build`

!!! success "Generated automation file"
    A new file will be created in your current directory `openai_api_playwright_huggingface_gen.py`, which contains the automation code needed to run the instructions outlined in the `huggingface.yaml` file.

You can create a new `yaml` file with your own `url` and `instructions` to test different actiosn on new sites!

!!! abstract "Playright configuration file"

    There are two key configuration options we need to specify to make a LaVague config file compatible with Playright instead of Selenium:

    1. Set `get_driver` option to our Playwright driver:
    `get_driver = default_get_playwright_driver`

    2. Set `prompt_template` to the default Playwright prompt template:
    `prompt_template = PLAYWRIGHT_PROMPT`