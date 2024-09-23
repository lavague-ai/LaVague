# Quick Tour

In this quick tour, we'll show how LaVague can be leveraged by:

- Builders to create custom automation pipelines
- QA engineers to automate the writing, maintenance, and execution of web tests  

## API key

To use LaVague, you will need an LaVague API key. You can get yours [here](https://cloud.lavague.ai/keys).

You will need to set your API key as a `LAVAGUE_API_KEY` environment variable in your working environment.

## Installation

We start by downloading the LaVague client SDK.

```bash
pip install lavague
```

## Automation

Let's see how we can use LaVague Web Agent's to automate filling in the following [sample job application form](https://form.jotform.com/241472287797370).

[⌛ GIF GOES HERE]

```python
from lavague.core.agents import WebAgent

# Create Web Agent
agent = WebAgent(api_key="")

# Optional user data to be used to fill in form
form_data = """
- job: product lead
- first name: John
- last name: Doe
- email: john.doe@gmail.com
- phone: 555-123-4567
- cover letter: Excited to work with you!
"""

# URL of form and objective to fill in form
url = "https://form.jotform.com/241472287797370"
obj = "Use the necessary data provided to fill in the form"

# Run agent
ret = agent.run(url=url, objective=obj, user_data=form_data)
```

In this example, we firstly import and initialize a LaVague `WebAgent`. We can then run our web task by using the WebAgent's `run` method. We pass it the`url` of the form we want to fill in, our natural language `objective`, and the information to be used to fill in the form through the **optional** `user_data` attribute.

LaVague's return object is called a `trajectory` and contains the list of actions performed to achieve the objective and information relating to the run.

We can then go to the visual web interface, or `Agent Studio`, by clicking on the outputted link to watch the generation of our web task live or review it a posteriori.

!!! info "Trajectory object"
    For full detailed on Trajectories & Actions, see our [Learn section]().

## QA

We can use LaVague agent's to create tests for websites.

If you prefer a quick no-code solution, you can use our [QA web interface](https://qa.lavague.ai). 

If you prefer to work directly with the code behind our web interface, read on!

Let's look at an example where we use LaVague to generate a `pytest` script checking the `add to cart` functionality of the `Amazon` website.

[⌛ GIF GOES HERE]

First of all, we need to get our `trajectory`, or series of actions, corresponding to the actions we want to test.

To do this, we initialize a WebAgent and give it an objective of testing a natural language `scenario`.

```python
from lavague.core.agents import WebAgent

# Create Web Agent
agent = WebAgent(api_key="")

# Optional user data to be used to fill in form
scenario = "Add the first product found when searching 'Nike SB-800 sneakers' to the basket."

# URL of form and objective to fill in form
url = "https://amazon.com/"
obj = "Test the following scenario + {scenario}"

# Run agent
ret = agent.run(url=url, objective=obj)
```

Again, a link will be output to review the trajectory generation in our `Agent Studio`.

Once we are happy with our trajectory, we can now use our `PyTestExporter` to convert the `trajectory` object returned from our WebAgent into a PyTest file that can be used for web testing.

```python
from lavague.exporter.selenium import PyTestExporter

# Detail test criteria
criteria = "Check there is one item in the user cart"

# Provide desired file name for test script
file_name = "Amazon_cart_test.py"

# Export trajectory to pytest script
exporter = PyTestExporter()
exporter.export(trajectory=ret, assert_criteria=criteria, file_name=file_name)
```

A replayable testing script for the Amazon cart feature will now be saved as `./Amazon_cart_test.py`.

??? info "Generated Amazon_cart_test.py"

    ```py
    import pytest
    from pytest_bdd import scenarios, given, when, then, parsers
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import ElementClickInterceptedException
    import time

    # Constants
    BASE_URL = "https://www.amazon.fr/"

    # Scenarios
    scenarios("demo_amazon.feature")


    # Fixtures
    @pytest.fixture
    def browser():
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()


    # Steps
    @given("the user is on the homepage")
    def user_on_homepage(browser):
        browser.get(BASE_URL)


    @when('the user clicks on "Accepter" to accept cookies')
    def accept_cookies(browser):
        accept_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div/span/form/div[2]/span/span/input")
            )
        )
        accept_button.click()


    @when(
        parsers.parse('the user enters "{search_term}" into the search bar and press Enter')
    )
    def enter_search_term(browser, search_term):
        search_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div/header/div/div/div[2]/div/form/div[3]/div/input")
            )
        )
        search_input.send_keys(search_term)
        search_input.submit()


    @when("the user clicks on the first product in the search results")
    def click_first_product(browser):
        first_product_link = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div/div/div/div/div/span/div/div[2]/div/div/span/div/div/div[2]/div/h2/a",
                )
            )
        )
        first_product_link.click()


    @when('the user clicks on the "Ajouter au panier" button')
    def add_to_cart(browser):
        add_to_cart_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div[2]/div/div[4]/div/div[5]/div[4]/div[4]/div/div/div/div/div/div/div/div/div[2]/div/form/div/div/div[23]/div/span/span/span/input",
                )
            )
        )
        add_to_cart_button.click()


    @when("the confirmation message is displayed")
    def confirm_message_displayed(browser):
        time.sleep(3)  # Wait for the confirmation message to be displayed


    @when('the user clicks on "Aller au panier" under "Passer la commande"')
    def go_to_cart(browser):
        go_to_cart_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div/div/div/div/div[2]/div/div[3]/div/div/span/span/a",
                )
            )
        )
        go_to_cart_button.click()


    @when('the user clicks on "Supprimer" from the cart page')
    def remove_from_cart(browser):
        remove_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div/div/div[3]/div[5]/div/div[2]/div/div/form/div[2]/div[3]/div[4]/div/div[2]/div/span[2]/span/input",
                )
            )
        )
        remove_button.click()


    @then("the cart should be empty")
    def cart_should_be_empty(browser):
        time.sleep(3)  # Wait for the cart update after removal
        empty_cart_message = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(text(), 'Your Amazon Cart is empty')]")
            )
        )
        assert (
            "Your Amazon Cart is empty" in empty_cart_message.text
        ), "Cart is not empty"
    ```

If later changes to the original website lead to our test becoming invalid, we can simply regenerate our `pytest` script by re-running the code to generate our script.

## Next steps

To understand the different components that make up LaVague, see our [architecture guide]().

For more examples, see our dedicated [automation]() & [QA]() example pages.