# QA Automation with LaVague and Pytest

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

??? note "Example file generated from a Gherkin test case"
    `test_cart.py` 
    ```python
    import pytest
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from pytest_bdd import scenarios, given, when, then

    # Constants
    BASE_URL = 'https://www.saucedemo.com/v1/inventory.html'

    # Scenarios
    scenarios('test_cart.feature')

    # Fixtures
    @pytest.fixture
    def browser():
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        driver.get(BASE_URL)
        yield driver
        driver.quit()

    # Steps
    @given('the user is on the home page')
    def user_on_home_page(browser):
        pass

    @when('the user clicks on a product')
    def user_clicks_on_product(browser):
        sauce_labs_backpack = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[2]/div/div[2]/div/div[1]/div[2]/a")
        try:
            browser.execute_script("arguments[0].click();", sauce_labs_backpack)
        except Exception as e:
            pytest.fail(f"Error clicking on product: {e}")

    @when('the user is on the product details page')
    def user_on_product_details_page(browser):
        pass

    @when('the user clicks on \'ADD TO CART\'')
    def user_clicks_add_to_cart(browser):
        add_to_cart_button = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[2]/div/div/div/button")
        try:
            browser.execute_script("arguments[0].click();", add_to_cart_button)
        except Exception as e:
            pytest.fail(f"Error clicking 'ADD TO CART': {e}")

    @when('the user clicks on the Cart icon')
    def user_clicks_cart_icon(browser):
        cart_icon = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/a")
        try:
            browser.execute_script("arguments[0].click();", cart_icon)
        except Exception as e:
            pytest.fail(f"Error clicking on Cart icon: {e}")

    @then('the user should see the item in the cart')
    def user_should_see_item_in_cart(browser):
        try:
            cart_item = browser.find_element(By.XPATH, "//*[@id='cart_contents_container']//div[@class='inventory_item_name' and text()='Sauce Labs Backpack']")
            assert cart_item.is_displayed(), "The item is not displayed in the cart"
        except Exception as e:
            pytest.fail(f"The item is not displayed in the cart: {e}")

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
