# QA Automation with LaVague and Pytest

- TODO: 
- Split into several files under the LaVague QA section
- Change gherkin and associated code to our best example (amazon?)
- Write the walkthrough based on lavague-qa/generator.py
- Update index.md
- Update README.md

## Use case

LaVague is a great tool to help you write and maintain automated tests more efficiently. Writing test scripts manually is time consuming, using recorders can help but scripts can break if the page structure changes. 

LaVague can generate reusable `pytest-bdd` code from a test case description written in `Gherkin`. If the page changes, simply re-run LaVague to update your test scripts.

## CLI quickstart


### Generate pytest files
We have built a CLI tool `lavague-qa` to help you run tests fast. 
Install it with `pip install lavague-qa`. Then run this example command to generate tests for
```sh
lavague-qa --url https://example.com --feature path/to/your_feature.feature
```

### Run the generated tests

```sh
pytest your_feature.py
```

## Features

LaVague is able to handle complex scenarios such as: 
```gherkin
Feature: Wikipedia Login

  Scenario: User logs in successfully
    Given the user is on the Wikipedia homepage
    When the user navigates to the login page
    And the user enters Lavague-test in the username field
    And the user enters lavaguetest123 in the password field
    And the user submits the login form
    Then the login should be successful and the user is redirected to the main page
```

Which results in this code:
??? note "Example code generated"
    `demo_wikipedia.py` 
    ```python
        import pytest
        from pytest_bdd import scenarios, given, when, then, parsers
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import ElementClickInterceptedException
        import time

        # Constants
        BASE_URL = 'https://en.wikipedia.org/'

        # Scenarios
        scenarios('demo_wikipedia.feature')

        # Fixtures
        @pytest.fixture
        def browser():
            driver = webdriver.Chrome()
            driver.implicitly_wait(10)
            yield driver
            driver.quit()

        # Steps
        @given('the user is on the Wikipedia homepage')
        def go_to_homepage(browser):
            browser.get(BASE_URL)

        @when('the user navigates to the login page')
        def navigate_to_login(browser):
            login_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/header/div[2]/nav/div/div[4]/div/ul/li[2]/a"))
            )
            try:
                browser.execute_script("arguments[0].click();", login_link)
            except ElementClickInterceptedException:
                pytest.fail("Failed to navigate to the login page")

        @when(parsers.parse('the user enters {username} in the username field'))
        def enter_username(browser, username):
            username_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div/div[2]/div/input"))
            )
            username_field.send_keys(username)

        @when(parsers.parse('the user enters {password} in the password field'))
        def enter_password(browser, password):
            password_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div[2]/div[2]/div/input"))
            )
            password_field.send_keys(password)

        @when('the user clicks on the login button under the username and password fields')
        def click_login_button(browser):
            login_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div[4]/div/button"))
            )
            try:
                browser.execute_script("arguments[0].click();", login_button)
            except ElementClickInterceptedException:
                pytest.fail("Failed to click the login button")

        @when('the user is redirected to the home page')
        def wait_for_homepage(browser):
            time.sleep(3)  # Wait for redirection

        @when('the user click on the username at the top of the page')
        def click_username(browser):
            username_link = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/header/div[2]/nav/div/div[2]/div/ul/li/a"))
            )
            try:
                browser.execute_script("arguments[0].click();", username_link)
            except ElementClickInterceptedException:
                pytest.fail("Failed to click on the username link")

        @then(parsers.parse('the URL should be "{expected_url}"'))
        def verify_url(browser, expected_url):
            current_url = browser.current_url
            assert current_url == expected_url, f"Expected URL to be {expected_url}, but got {current_url}"
    ```

## Demo

TODO


## CLI Usage

Run `lavague-qa --help` to show available arguments

```
Usage: lavague-qa [OPTIONS]

Options:
  -u, --url TEXT      URL of the site to test
  -f, --feature TEXT  Path to the .feature file containing Gherkin
  -h, --headless      Enable headless mode for the browser
  -db, --log-to-db    Enables logging to a SQLite database
  --help              Show this message and exit.
```

!!! tips "Pre-requisites"

    We use OpenAI's models, for the embedding, LLM and Vision model. You will need to set the **OPENAI_API_KEY** variable in your local environment with a valid API key for this example to work.

### Run it with your feature file
1. Create a `.feature` file containing valid Gherkin test steps
2. Run `lavague-qa --url https://example.com --feature path/to/gherkin/feature`

### Default example
Run `lavague-qa` to run the default wikipedia.org example [available here](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/demo_wikipedia.feature)


## Walkthrough

We will walkthrough the [TestGenerator](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/lavague/qa/generator.py) class logic. It leverages LaVague agents to run tests on a website, records selector data and rebuilds the pytest file. 


## Script walk through

Let's walk through some of the core components of our script to give you a better understanding of how we use LaVague to make you more efficient at testing your web apps. 


### Main logic

To generate the test, we go through the following steps:
- load and parse the Gherkin file
- run the LaVague agent with the objective to run the test scenario
- use recorded data to build a prompt
- use an LLM to build the pytest


### Starting from Gherkin scenarios and an URL

Gherkin is a language used in behavior-driven development (BDD) to describe feature behavior. 

Several example `.feature` files are [available here](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/).


```gherkin
Feature: Cart

  TODO: add example feature
```



### Running a test case with a LaVague agent

In order to record all information needed to generate a robust test case, we run each scenario with LaVague.



## Running our tests

Assuming you are still in the same directory, you can simply use `pytest name_of_the_generated_file.py}` to run the generated tests.

## Limitations and next steps

!!! warning "Verify the code"

    100% accuracy is not guaranteed and we advise you review the generated final code file

**Main limitation**: LaVague sometimes struggle on complex JavaScript heavy websites because of the difficulty of identifying the right selector. Try to rerun the agent if it fails. 

**Going further**:

- Add support for other testing frameworks
- Generate Gherkin file from higher level instructions
- Integrate LaVague in the life cycle of your tests

## Need help ? Found a bug ?
Join our [Discord](https://discord.gg/invite/SDxn9KpqX9) to reach our core team and get support!
