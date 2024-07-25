
# LaVague Testing Documentation

The `lavague-tests` command-line interface (CLI) facilitates the testing and benchmarking of LaVague across a variety of common use cases.

## Installation

Install the CLI tool via pip:

```bash
pip install lavague-tests
```

## Quick Start Examples

### Example 1 (no arguments)

By default, `lavague-tests` will run all tests defined in `/sites` with the default set of LLMs (`gpt-4o`)

```bash
> lavague-tests
```

Output

```
Result: 80 % (8 / 10) in 183.7s
Tokens: 155963 (0.9255 $)
```

### Example 2 (one site only, custom set of LLMs)
To test LaVague with a custom site, in this case `amazon.com`, and a custom configuration (custom Large Language Models (LLMs) defined in `custom_context.py`), you can use the `--site` or `-s` and `--context` or `-c` options:

```bash
lavague-tests -s amazon.com -c lavague-tests/contexts/custom_context.py
```

Output

```
Result: 100 % (2 / 2) in 59.88s
Tokens: 41872 (0.2229 $)
```

## Usage

Display help and command-line options:

```bash
❯ lavague-test --help
Usage: lavague-test [OPTIONS]

Options:
  -c, --context TEXT    Python file containing an initialized context and token_counter. Default is context/default_context.py
  -d, --directory TEXT  Sites directory
  -s, --site TEXT       Site name
  --display             If set, the browser will be displayed
  -db, --log-to-db      If set, enables logging to the default SQLite database
  --help                Show this message and exit.
```

## Command-Line Options Overview

| Option       | Alias | Description   | Default Value   | Required |
| ------------ | ------| ------------- | --------------- | -------- |
| `--context`  | `-c`  | Path to a Python file containing an initialized `Context` and `TokenCounter`. | `./lavague-tests/contexts/default_context.py` | No |
| `--directory`| `-d`  | Directory where the site configurations are stored. | `./lavague-tests/sites` | No |
| `--site`     | `-s`  | Name of the site(s) to test. Multiple sites can be specified. | All sites in `./lavague-tests/sites` | No |
| `--display`  | None  | If set, displays the browser during the test. | False | No |
| `--log-to-db`| `-db` | If enabled, logs test results to the default SQLite database. | False | No |

## Custom Use Cases Configuration in `/sites`

To define custom use cases, create configuration files within the `sites/` directory. Each site should have its own folder and a `config.yml` file specifying the tasks to execute during testing.

### Example Configuration Structure

```yaml
tasks:
  - name: Task name (optional)
    url: URL to test
    prompt: Description of the task
    expect:
      - Conditions for successful test completion
```

## Custom Contexts Definition in `/contexts`

To define custom LLMs for test cases, create a `.py` file in `/contexts` containing the `context` and `token_counter` variables. We provide a default context (uses `gpt-4o`) and a custom example.

### Example `custom_context.py`

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
