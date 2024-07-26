
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytest_bdd import scenarios, given, when, then

# Constants
BASE_URL = 'https://www.amazon.fr/'

# Scenarios
scenarios('demo.feature')

# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    driver.get(BASE_URL)
    yield driver
    driver.quit()

# Steps
@given('I am on the homepage')
def i_am_on_the_homepage(browser):
    pass

@when('I click "Accepter" to accept cookies')
def i_click_accept_cookies(browser):
    try:
        accept_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/span/form/div[2]/span/span/input"))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", accept_button)
        accept_button.click()
    except Exception as e:
        pytest.fail(f"Failed to click accept cookies button: {e}")

@when('I enter "Harry Potter et la Chambre des Secrets" into the search bar and press Enter')
def i_enter_search_query(browser):
    try:
        search_bar = browser.find_element(By.XPATH, "/html/body/div/header/div/div/div[2]/div/form/div[3]/div/input")
        search_bar.send_keys("Harry Potter et la Chambre des Secrets")
        search_bar.send_keys(u'\ue007')  # Press Enter key
    except Exception as e:
        pytest.fail(f"Failed to enter search query: {e}")

@when('I click on "Harry Potter et la Chambre des Secrets" in the search results')
def i_click_search_result(browser):
    try:
        search_result = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/div/span/div/div[3]/div/div/span/div/div/div/span/a"))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", search_result)
        search_result.click()
    except Exception as e:
        pytest.fail(f"Failed to click search result: {e}")

@when('I am on the product details page')
def i_am_on_product_details_page(browser):
    pass

@when('I click on the "Ajouter au panier" button')
def i_click_add_to_cart(browser):
    try:
        add_to_cart_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[4]/div/div[5]/div[4]/div[4]/div/div/div/div/div/div/div/div/div/form/div/div/div/div/div[4]/div/div[23]/div/span/span/span/input"))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", add_to_cart_button)
        add_to_cart_button.click()
    except Exception as e:
        pytest.fail(f"Failed to click add to cart button: {e}")

@when('I am taken to a confirmation page')
def i_am_taken_to_confirmation_page(browser):
    pass

@when('I click on "Aller au panier"')
def i_click_go_to_cart(browser):
    try:
        go_to_cart_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/div[2]/div/div[3]/div/div/span/span/a"))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", go_to_cart_button)
        go_to_cart_button.click()
    except Exception as e:
        pytest.fail(f"Failed to click go to cart button: {e}")

@when('I am taken to the cart page')
def i_am_taken_to_cart_page(browser):
    pass

@when('I remove the product from the cart by clicking on "Supprimer"')
def i_remove_product_from_cart(browser):
    try:
        remove_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[3]/div[5]/div/div[2]/div/div/form/div[2]/div[3]/div[4]/div/div[2]/div/span[2]/span/input"))
        )
        browser.execute_script("arguments[0].scrollIntoView(true);", remove_button)
        remove_button.click()
    except Exception as e:
        pytest.fail(f"Failed to click remove button: {e}")

@then('the cart should be empty')
def the_cart_should_be_empty(browser):
    try:
        empty_cart_message = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Votre panier Amazon est vide.')]"))
        )
        assert empty_cart_message.is_displayed()
    except Exception as e:
        pytest.fail(f"Cart is not empty: {e}")
