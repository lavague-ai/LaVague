# Test runner for LaVague

LaVague Test Runner is a tool designed to run tests on real websites and generate comprehensive reports. It can be easily launched using the lavague-test command.

## Usage

To run the LaVague Test Runner, use the lavague-test command. Below are the available options and their descriptions:

### Command Options

- --directory / -d
  - Default: current working directory + "/lavague-tests/sites"
  - Type: str
  - Description: Specifies the directory where the site test files are located.

- --site / -s
  - Default: test on all sites described in -d directory
  - Type: str
  - Description: Specifies the site names to run tests on. This option can be used multiple times to specify multiple sites.

- --display
  - Type: flag
  - Description: If set, the browser will be displayed during the tests.


### Site Test Folder Structure

Each site to be tested must be a folder containing a `config.yml` file with the test configuration. Below is an example structure:

```arduino
lavague-tests/sites/
└── example-site/
    └── config.yml
```

The config.yml file define tasks with the following structure:

```yaml
type: web
max_steps: 5                      # max number of action engine retry
n_attempts: 1                     # max number of agent retry
user_data:                        # optional user data to feed the Agent
  key: value
tasks:
  - name: Name                    # Optional display name
    max_steps: 5                  # to override global value
    n_attempts: 1                 # to override global value
    url: https://example.com      # the intial task URL
    prompt: Prompt for the agent  # the agent prompt
    expect:                       # the list of tests to perform on task completion, see below for details
      - <property> <operator> <value>
    user_data:                    # optional task-scoped user data to feed the Agent
      key: value
```


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


## Output

`lavague-test` will output a report with successes and failures.
If all tests passed exit code will be 0, and -1 if at least one test failed.

Example:
```text
[o] HuggingFace navigation
        URL is https://huggingface.co/docs/peft/quicktour
        Status is success
        HTML contains PEFT offers parameter-efficient methods for finetuning large pretrained models

[o] HuggingFace search
        URL is https://huggingface.co/datasets/BigAction/the-wave-250
        Status is success

[x] Go to LaVague.ai from https://google.com
    (x) URL is https://lavague.ai - was: https://www.google.com/
    (x) Status is success - was: failure

[o] Navigate using link
        URL is http://localhost:8000/menu.html
        Status is success
        HTML contains <h1>Menu</h1>

Result: 80 % (8 / 10)
```

## Use with static local website

In `config.yml` set `type` to `static` to serve a static website locally.

The following options are available:
- directory : the directory to serve files from. Defaults to `www` ;
- port : the port to serve the files on. Defaults to 8000.

## Use with dynamic local website

Initialization command for local websites will be available soon.