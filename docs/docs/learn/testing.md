
# LaVague Testing Documentation

The `lavague-tests` command-line interface (CLI) facilitates the testing and benchmarking of LaVague across a variety of common use cases.

## Installation

Install the CLI tool via pip:

```bash
pip install lavague-tests
```

## Quick Start

### Default tests

By default, `lavague-test` will run all tests defined in `/sites` with the default `OpenAI Context`.

The`/sites` folder contains is already populated with several tests which cover a range of popular websites and use cases.

You can test out the performance of LaVague on these tests with the following command:

!!! warning "Running lavague-test"
    Note that in order to use the default configuration, you will need to run `lavague-test` from the root of the LaVague repo.

```bash
> lavague-test
```

??? note "Command line options overview"

    | Option       | Alias | Description   | Default Value   | Required |
    | ------------ | ------| ------------- | --------------- | -------- |
    | `--context`  | `-c`  | Path to a Python file containing an initialized `Context` and `TokenCounter`. | `./lavague-tests/contexts/default_context.py` | No |
    | `--directory`| `-d`  | Directory where the site configurations are stored. | `./lavague-tests/sites` | No |
    | `--site`     | `-s`  | Name of the site(s) to test. Multiple sites can be specified. | All sites in `./lavague-tests/sites` | No |
    | `--display`  | None  | If set, displays the browser during the test. | False | No |
    | `--log-to-db`| `-db` | If enabled, logs test results to the default SQLite database. | False | No |

The output of this command is a report including information on which tasks succeeded or failed, the percentage of tests that succeeded and a table outlining the token consumption and estimated total cost of these tests:

```
Result: 78 % (18 / 23) in 727.5s

Component        | Input      | Output     | Total      | Cost (USD) |
----------------------------------------------------------------------
World Model      | 128688     | 3655       | 132343     | $ 0.6983   |
Action Engine    | 256960     | 6577       | 263537     | $ 1.3835   |
Embeddings       | 3732520    |            | 3732520    | $ 0.4852   |
----------------------------------------------------------------------
Total            | 4118168    | 10232      | 4128400    | $ 2.5669   |

```

### Selecting which sites to test

You can select to run `lavague-test` on just one or several sites defined in the `sites` folder by specifying the sites to be tested with the `--site` or `-s` option. Note this site name much match a corresponding folder containing a test configuration file in the `lavague-tests/sites` folder.

```bash
lavague-test -s amazon.com -s youtube.com
```

### Testing LaVague with a built-in context

We provide the following configuration files for running your tests with alternative built-in configurations:

- For testing with `Anthropic's Claude 3.5 Sonnet`: lavague-tests/contexts/anthropic_context.py
- For testing with ` Llama3.1 405B via the Fireworks API`: lavague-tests/contexts/fireworks_context.py
- For testing with `Gemini`: lavague-tests/contexts/gemini_context.py

You can provide these config files as an argument to our `lavague-test` command to run tests with these built-in configuration files:

```bash
lavague-test-c lavague-tests/contexts/anthropic_context.py
```

> Note, you will need to set the relevant API keys and install the relevant lavague pypi packages (lavague-contexts-anthropic, lavague-contexts-fireworks or lavague-contexts-gemini) for these to work.

### Providing a custom configuration file

To define your own custom context, you can create a `.py` file in the `lavague-tests/contexts` folder. Within this file, you should define a `context` and `token_counter` variable.

The `context` variable should be a `Context` which you can create with the `llm`, `mm_llm` and `embedding` of your choice. These models should be instances of a `llama_index.llms`, `llama_index.multi_modal_llms` and `llama_index.embeddings` models respectively.

#### Custom configuration file example

```python
from lavague.core.token_counter import TokenCounter
from llama_index.llms.openai import OpenAI
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.embeddings.openai import OpenAIEmbedding
from lavague.core.context import Context

llm_name = "gpt-4o-mini"
mm_llm_name = "gpt-4o-mini"
embedding_name = "text-embedding-3-large"

token_counter = TokenCounter()

# Initialize models
llm = OpenAI(model=llm_name)
mm_llm = OpenAIMultiModal(model=mm_llm_name)
embedding = OpenAIEmbedding(model=embedding_name)

# Initialize context
context = Context(llm, mm_llm, embedding)
```

## How to add your own tests

To add a custom test, you will need to add a folder named after the site you will test within the `sites/` directory. 

Each site folder should contain a `config.yml` file specifying the tasks to execute during testing.

The config.yml file has a `tasks:` option, within which you should define the tests to be run and any configuration for these tasks:

```yaml
tasks:
  - name: Name                    # Optional display name
    max_steps: 5                  # to override global value
    n_attempts: 1                 # to override global value
    url: https://example.com      # the initial task URL
    prompt: Prompt for the agent  # the agent prompt
    expect:                       # the list of tests to perform on task completion, see below for details
      - <property> <operator> <value>
    user_data:                    # optional task-scoped user data to feed the Agent
      key: value
```

> You can also set any options globally such as `max_steps` or `n_attempts` above the `tasks` option. These will be overwritten by any task-specific options of the same type.

### Available operators:

| Operator          | Python operation      |
|-------------------|-----------------------|
| is                | operator.eq           |
| is not            | operator.ne           |
| is lower than     | operator.lt           |
| is greater than   | operator.gt           |
| contains          | operator.contains     |
| does not contain  | not operator.contains |


### Available properties:

| Property | Type              |
|----------|-------------------|
| URL      | string            |
| Status   | success / failure |
| Output   | string            |
| Steps    | number            |
| HTML     | string            |
| Tabs     | string            |

Example of `config.yml`

```yaml
tasks:
  - name: HuggingFace navigation
    url: https://huggingface.co/docs
    prompt: Go on the quicktour of PEFT
    expect:
      - URL is https://huggingface.co/docs/peft/quicktour
      - Status is success
      - HTML contains PEFT offers parameter-efficient methods for finetuning large pretrained models
  - name: HuggingFace search
    url: https://huggingface.co
    prompt: Find the-wave-250 dataset
    expect:
      - URL is https://huggingface.co/datasets/BigAction/the-wave-250
      - Status is success
```

??? science "Testing on your static website"

    To test with a static website, you can add the following options to your task within you `config.yml`:

    - type: static
    - directory : the directory to serve files from. Defaults to `www` which is expected in the same folder as your `config.yml`
    - port : the port to serve the files on. Defaults to 8000

## Contributing your tests

We would like to add your tests to our set of default tests, enabling us to build a wide-ranging collection of tests reflecting our communities needs and interests.

To do so, you will need to:

- Clone the LaVague repo.
- Add a test website folder to the `lavague-tests/sites` folder: e.g. For a test of `yahoo.com`, you should add a `yahoo.com` folder in the `sites` directory.
- Add your config.yml file defining your test in this folder.
- Push your additions and create a PR to the main LaVague repo.

For more information on how to submit a PR to the repo, see [our contribution guide](https://docs.lavague.ai/en/latest/docs/contributing/general/).