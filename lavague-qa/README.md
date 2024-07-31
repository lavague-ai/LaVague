# Test runner for LaVague

LaVague-QA is a specialized tool to generate pytest files from Gherkin test descriptions. 

## Usage

```
Usage: lavague-qa [OPTIONS]

Options:
  -u, --url TEXT      URL of the site to test
  -f, --feature TEXT  Path to the .feature file containing Gherkin
  -h, --headless      Enable headless mode for the browser
  -db, --log-to-db    Enables logging to a SQLite database
  --help              Show this message and exit.
```


Examples are provided in `./features/`:
```bash
lavague-qa --url https://amazon.com/ --feature features/demo_amazon.feature
```
Run `lavague-qa` to run a default example: Wikipedia login test

