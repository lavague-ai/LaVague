# Quick Tour

LaVague is an AI Agent framework to automate web interactions. Our core technology leverages LLMs to understand and navigate the web to perform actions for the sake of users.

LaVague can be used to offload many tasks, from testing websites for QA engineers to automating information retrieval on complex websites through filling complex forms automatically.

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

![form](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/form.png)

```python
from lavague.core.agents import WebAgent

# Create Web Agent
agent = WebAgent(world_model, action_engine)

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

Here, we:

- Initialize our LaVague agent option
- Run our web task by using the Agent's `run` method, passing it the`url` of the form, our natural language `objective` to fill in the form, and the information to be used to fill in the form through the **optional** `user_data` attribute.

LaVague's return object is called a Trajectory and contains the list of actions performed to achieve the objective and information relating to the run, including:

- `results`: A list of actions and information relevant to individual actions.
- `output`: A final text output from the agent, where relevant.
- `status`: Where the Agent run was `completed` without an Exception being thrown or `failed`

Each `action` in results contains a `preaction_screenshot` and `postaction_screenshot` with a screenshot taken before and after action is performed.

> For full detailed on Trajectories & Actions, see our [Learn section]().

Let's review the screenshot of the webpage after our task was ran.

```python
# Show screenshot of remote browser after running LaVague
from PIL import Image

last_action = ret.results[-1:]
img = Image.open(last_action["postaction_screenshot"])
img.show()
```
![after screenshot](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/screenshot-form.png)

Feel free to try automating different actions on the web by using the above code and modifying the `url` and `objective` to any website and objective of your choice.

## QA

We can use LaVague agent's to create tests for websites.

If you prefer a quick no-code solution, you can use our [QA web interface] (https://qa.lavague.ai). If you prefer to work directly with the code behind our web interface, read on!

Let's look at an example where we use LaVague to generate a `pytest` script checking the `add to cart` functionality of the `Amazon` website.

First of all, we need to get our `trajectory`, or series of actions, corresponding to the actions we want to test.

To do this, we initialize our agent and ask it to test a natural language `scenario`.

```python
from lavague.core.agents import WebAgent

# Create Web Agent
agent = WebAgent(world_model, action_engine)

# Optional user data to be used to fill in form
scenario = "Add the first product found when searching 'Nike SB-800 sneakers' to the basket."

# URL of form and objective to fill in form
url = "https://amazon.com/"
obj = "Test the following scenario + {scenario}"

# Run agent
ret = agent.run(url=url, objective=obj)
```

We can now use our `PyTestExporter` to convert the `trajectory` created by our Agent into a PyTest file that can be used for web testing.

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

## Roadmap

Currently, we only provide one `exporter` for LaVague trajectories, the `PyTestExporter` seen in the QA section of this quick tour, which converts trajectories into PyTest files to test a series of actions on a web page.

We are working on building more exporters, so keep an eye on our Discord and GitHub for the release of new `exporters`. We also want to encourage the community to help us to build and contribute new exporters for your use cases!

## Get in touch

If you have any feedback or need any support getting started with LaVague, please [get in touch](https://www.lavague.ai/contact).