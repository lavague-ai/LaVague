# LaVague QA: Usage guide

!!! warning "Early release"
    LaVague QA is still a work in progress and may contain bugs. Join our [community of amazing contributors](https://discord.gg/invite/SDxn9KpqX9) to help make this tool more reliable!

## Installation

LaVague QA uses `gpt-4o` models by default, as such, you will need to define `OPENAI_API_KEY` as an environment variable before running LaVague. 

### Install with pip

Install the latest release of our package with `pip`

```
pip install lavague-qa
```

### Install from source

Install from the latest repository source

Clone the [LaVague](https://github.com/lavague-ai/LaVague) repository

```sh
git clone https://github.com/lavague-ai/LaVague.git
```

Navigate to the `lavague-qa` package
```
cd LaVague/lavague-qa
```

Install with pip
```
pip install -e .
```


## Default usage

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/LaVague/blob/main/lavague-qa/demo_lavague_QA.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>

Run `lavague-qa --help` to see all available arguments

```
Usage: lavague-qa [OPTIONS]

Options:
  -u, --url TEXT      URL of the site to test
  -f, --feature TEXT  Path to the .feature file containing Gherkin
  -l, --full-llm      Enable full LLM pytest generation
  -c, --context TEXT  Path of python file containing an initialized context
                      and token_counter. Defaults to OpenAI GPT4o
  -h, --headless      Enable headless mode for the browser
  -db, --log-to-db    Enables logging to a SQLite database
  --help              Show this message and exit.
```

Run `lavague-qa` with a `URL` and a `.feature` file to generate tests

!!! tip "OPENAI_API_KEY"
    If you haven't already set a valid OpenAI API Key as the `OPENAI_API_KEY` environment variable in your local environment, you will need to do that now.

```bash
lavague-qa --url https://example.com --feature example.feature
```

LaVague will create a new directory containing your feature file and the python file

```
- Feature file: ./generated_tests/example.feature
- Pytest file: ./generated_tests/example.py

Tests successfully generated
 - Run `pytest ./generated_tests/example.py` to run the generated test.
```

Run the tests with `pytest` to validate their behavior

```bash
pytest ./generated_tests/example.py
=========================== test session starts ===========================
platform darwin -- Python 3.10.14, pytest-8.2.1, pluggy-1.5.0
rootdir: /Users/
configfile: pyproject.toml
plugins: anyio-4.3.0, bdd-7.1.2
collected 1 item                                                                                                                                                                                                                                         

generated_tests/example.py .                                                                                                                                                                                                               [100%]

=========================== 1 passed in 16.03s ===========================

```


## Customization

By default, LaVague attempts to minimize reliance on LLMs in order to optimize costs.

### Flag `--context` or `-c`

Contexts are used to define the set of LLMs that will be used by LaVague QA to generate tests.

Contexts are defined in `.py` configuration files which instantiate the required `Context` object and a `TokenCounter` object.

- By default we use our OpenaiContext which leverages OpenAI's `gpt-4o` and `text-embedding-3-small`
- You can learn how to define a custom context with models of your choice [in this guide](https://docs.lavague.ai/en/latest/docs/get-started/testing/#providing-a-custom-configuration-file)

To run with a custom context, use the `--context` flag along with the path to the `.py` file creating the objects.

```bash
lavague-qa --context ./my_contexts/custom_context_gemini.py
```

### Flag `--full-llm` or `-l`

By default, when this flag is not set, we build 90% of the pytest file deterministically and only rely on LLMs for the assert generation. 

However, sometimes this can lead to LaVague taking extra steps that are not defined in the Gherkin. In this case, Pytest building will fail as the number of instructions ran by the agent is different from the number of actions defined in the Gherkin. 

In this case, you can use the `-l` or `--full-llm` flag to generate the entire Pytest file with an LLM (and not the just the assert statement).

```bash
lavague-qa --full-llm --url https://example.com --feature example.feature
```

This will create `example_llm.py` that you can run with Pytest.

## Learn more

- Learn about advanced usage and customization in our [Example section](./examples.md)

Join our [Discord](https://discord.gg/invite/SDxn9KpqX9) to reach our core team and get support!