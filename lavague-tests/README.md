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

Example config.yml
The config.yml file should define tasks with the following structure:

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