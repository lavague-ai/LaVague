# LaVague testing

Our `lavague-tests` CLI can help you test and benchmark LaVague on common use cases.

## Example

Run LaVague on the amazon.com test cases with a custom set of LLMs defined in `custom_context.py`

```bash
lavague-tests -s amazon.com -c lavague-tests/contexts/custom_context.py
```

Output
```
Result: 100 % (2 / 2) in 59.88s
Tokens: 41872 (0.2229 $)
```

## Installation

To use the CLI tool install it with `pip`: 
```
pip install lavague-tests
```

## Usage

```bash
❯ lavague-test --help
Usage: lavague-test [OPTIONS]

Options:
  -c, --context TEXT    python file containing an initialized context and
                        token_counter. Default is context/default_context.py
  -d, --directory TEXT  sites directory
  -s, --site TEXT       site name
  --display             if set browser will be displayed
  -db, --log-to-db      if set, enables logging to the default SQLite database
  --help                Show this message and exit.
```

## Command-Line Options


| Option       | Alias | Description   | Default Value   | Required |
| ------------ | ------------ | ------------- | --------------- | -------- |
| `--context` | `-c` | Path to a Python file containing an initialized `Context` and `TokenCounter`. | `{current_dir}/lavague-tests/contexts/default_context.py` | No |
| `--directory` | `-d` | Directory where the sites configurations are stored. | `{current_dir}/lavague-tests/sites` | No |
| `--site` | `-s` | Name(s) of specific sites to test. Multiple sites can be specified. | All sites in `lavague-tests/sites` | No |
| `--display` | NA | If set, the browser will be displayed during the test. | False | No |
| `--log-to-db` | `-db` | If set, enables logging test results to the default SQLite database. | False | No |

## Defining Custom Use Cases in `/sites`

To define custom use cases for your testing tool, you need to create configuration files within the `sites/` directory. Each site should have its own folder and a `config.yml` file where you specify tasks that the tool should execute during testing.

### Configuration Structure

Each configuration file should follow this basic structure:

```yaml
tasks:
  - name: Task name (optional)
    url: URL to test
    prompt: Description of what the task is meant to simulate
    expect:
      - Conditions to be met for the test to be considered successful
```


