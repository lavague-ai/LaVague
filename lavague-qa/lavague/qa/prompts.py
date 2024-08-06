from llama_index.core import PromptTemplate


PYTEST_HEADER_TEMPLATE = PromptTemplate(
    """
import pytest
from pytest_bdd import scenarios, given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Constants
BASE_URL = '{url}'

# Scenarios
scenarios('{feature_file_name}')

# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# Steps
"""
)

PYTEST_GIVEN_TEMPLATE = PromptTemplate(
    """@given('{step}')
def {method_name}(browser: webdriver.Chrome):
    {code}
"""
)

PYTEST_WHEN_TEMPLATE = PromptTemplate(
    """@when('{step}')
def {method_name}(browser: webdriver.Chrome):
{actions_code}
"""
)

PYTEST_THEN_TEMPLATE = PromptTemplate(
    """@then('{step}')
def {method_name}(browser: webdriver.Chrome):
{assert_code}
"""
)


FULL_PROMPT_TEMPLATE = PromptTemplate(
    """You are an expert in software testing frameworks and Python code generation. You answer in python markdown only and nothing else.
Your only goal is to generate pytest-bdd files based on the provided Gherkin feature, a collection of instructions and actions, and a specific assert statement to test.
You will use the provided information to generate a valid assert statement. 
- Name the scenario appropriately.
- Always use time.sleep(3) if waiting is required.
- Include all necessary imports and fixtures.
- Use provided actions to find valid XPath selectors for the final pytest file. 
- You answer in python code only and nothing else.

I will provide an example below:
----------
Feature file name: example.feature

URL: https://www.example.com

Gherkin of the feature to be tested: 

Feature: E-commerce Website Interaction

  Scenario: Browse products and checkout
    Given I am on the example website
    When I navigate to the product catalog
    And I filter products by category
    And I sort products by price
    And I add a random product to the cart
    And I proceed to checkout
    Then the cart total should be correct

Assert statement Then the cart total should be correct

List of already executed instructions and actions:
- instruction: Navigate to the product catalog page
  actions:
    - action:
        name: "click"
        args:
          xpath: "/html/body/div[1]/header/nav/ul/li[3]/a"
          value: ""

- instruction: Select a category from the dropdown filter
  actions:
    - action:
        name: "click"
        args:
          xpath: "/html/body/div[2]/main/div/div[1]/aside/div[3]/select/option[3]"
          value: ""

- instruction: Sort products by price
  actions:
    - action:
        name: "click"
        args:
          xpath: "/html/body/div[2]/main/div/div[2]/div[1]/div/button[2]"
          value: ""

- instruction: Add a random product to the cart
  actions:
    - action:
        name: "click"
        args:
          xpath: "/html/body/div[2]/main/div/div[2]/ul/li[5]/div/button[@data-testid='add-to-cart']"
          value: ""

- instruction: Proceed to checkout
  actions:
    - action:
        name: "click"
        args:
          xpath: "/html/body/div[1]/header/div[2]/div/div/a"
          value: ""
          
          
Resulting pytest code: 
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time
import random

# Constants
BASE_URL = 'https://example.com'

# Scenarios
scenarios('complex_example.feature')

# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# Steps
@given('I am on the example website')
def go_to_homepage(browser):
    browser.get(BASE_URL)

@when('I navigate to the product catalog')
def navigate_to_catalog(browser):
    catalog_link = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/header/nav/ul/li[3]/a"))
    )
    try:
        browser.execute_script("arguments[0].click();", catalog_link)
    except ElementClickInterceptedException:
        pytest.fail("Failed to navigate to the product catalog")

@when('I filter products by category')
def filter_products(browser):
    category_dropdown = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/main/div/div[1]/aside/div[3]/select"))
    )
    options = category_dropdown.find_elements(By.TAG_NAME, "option")
    random_option = random.choice(options[1:])  # Exclude the first option if it's a placeholder
    random_option.click()

@when('I sort products by price')
def sort_products(browser):
    sort_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div/div[2]/div[1]/div/button[2]"))
    )
    try:
        browser.execute_script("arguments[0].click();", sort_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to sort products")

@when('I add a random product to the cart')
def add_to_cart(browser):
    products = browser.find_elements(By.XPATH, "/html/body/div[2]/main/div/div[2]/ul/li")
    random_product = random.choice(products)
    add_to_cart_button = random_product.find_element(By.XPATH, ".//button[@data-testid='add-to-cart']")
    try:
        browser.execute_script("arguments[0].click();", add_to_cart_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to add product to cart")

@when('I proceed to checkout')
def proceed_to_checkout(browser):
    checkout_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/header/div[2]/div/div/a"))
    )
    try:
        browser.execute_script("arguments[0].click();", checkout_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to proceed to checkout")

@then('I should see the checkout form')
def verify_checkout_form(browser):
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "checkout-form"))
        )
    except Exception as e:
        pytest.fail("Checkout form not found: " + str(e))

@then('the cart total should be correct')
def verify_cart_total(browser):
    try:
        total_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "cart-total"))
        )
        total_value = float(total_element.text.replace('$', ''))
        assert total_value > 0, "Cart total should be greater than zero"
    except Exception as e:
        pytest.fail("Failed to verify cart total" + str(e))

@then('the product list should be visible')
def verify_product_list(browser):
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-list"))
        )
    except Exception as e:
        pytest.fail("Product list not found: " + str(e))

@then('the category filter should be available')
def verify_category_filter(browser):
    try:
        filter_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "category-filter"))
        )
        assert filter_element.is_enabled(), "Category filter should be enabled"
    except Exception as e:
        pytest.fail("Category filter not found or not enabled: " + str(e))

@then('the "Add to Cart" button should be present for each product')
def verify_add_to_cart_buttons(browser):
    try:
        add_to_cart_buttons = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-testid='add-to-cart']"))
        )
        assert len(add_to_cart_buttons) > 0, "No 'Add to Cart' buttons found"
    except Exception as e:
        pytest.fail("Failed to verify 'Add to Cart' buttons: " + str(e))

----------
Given this information, generate a valid pytest-bdd file with the following inputs:
Feature file name: {feature_file_name}
URL: {url}
Gherkin of the feature to be tested:{feature_file_content}
Assert statement: {expect}\n
Potentially relevant nodes that you may use to help you generate the assert code: {nodes}\n
List of already executed instructions and actions:\n
{actions}\n
"""
)

ASSERT_ONLY_PROMPT_TEMPLATE = PromptTemplate(
    """You are an expert in software testing frameworks and Python code generation. You answer in python markdown only and nothing else.
Your only goal is to use the provided Gherkin and HTML nodes to generate a valid pytest-bdd python assert statement. 
- Include all necessary imports and fixtures.
- If element selection is needed, prefer XPath based on class or text content to fetch it. 
- You answer in python code only and nothing else.
- You have access to a browser variable of type selenium.webdriver.chrome.webdriver.Chrome

```python
browser: WebDriver
# assert code here
```

I will provide an example below:
----------
Gherkin: Then the cost should be "34,70 €"
HTML: <div><span>Cost:</span><span class="calculator__cta__price">34,70 €</span></div>
                
Resulting pytest code: 
cost_element = WebDriverWait(browser, 10).until(
    EC.presence_of_element_located((By.XPATH, "//span[@class='calculator__cta__price']"))
)
actual_cost = cost_element.text.strip()
assert actual_cost == expected_cost

----------
Given this information, generate a valid pytest-bdd assert instruction with the following inputs:
Gherkin expect of the feature to be tested: Then {expect}\n
Potentially relevant HTML that you may use to help you generate the assert code: {html_chunks}\n
"""
)
