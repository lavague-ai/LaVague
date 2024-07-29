
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time

# Constants
BASE_URL = 'https://www.amazon.fr/'

# Scenarios
scenarios('demo_amazon.feature')

# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# Steps
@given('I am on the homepage')
def go_to_homepage(browser):
    browser.get(BASE_URL)
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

@when('I click "Accepter" to accept cookies')
def click_accept_cookies(browser):
    button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/span/form/div[2]/span/span/input"))
    )
    try:
        browser.execute_script("arguments[0].click();", button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click the 'Accepter' button")

@when(parsers.parse('I enter "{search_text}" into the search bar and press Enter'))
def enter_search_text(browser, search_text):
    search_bar = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/header/div/div/div[2]/div/form/div[3]/div/input"))
    )
    search_bar.clear()
    search_bar.send_keys(search_text)
    search_bar.submit()

@when('I click on the first book in the search results')
def click_first_book(browser):
    first_book = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/div/span/div/div[4]/div/div/span/div/div/div/span/a/div"))
    )
    try:
        browser.execute_script("arguments[0].click();", first_book)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click the first book in the search results")

@when('I click on the "Ajouter au panier" button')
def click_add_to_cart(browser):
    add_to_cart_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[4]/div/div[5]/div[4]/div[4]/div/div/div/div/div/div/div/div/div/div/div/div/div[2]/div/form/div/div/div[23]/div/span/span/span/input"))
    )
    try:
        browser.execute_script("arguments[0].click();", add_to_cart_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click the 'Ajouter au panier' button")

@when('I click on "Aller au panier" under "Passer la commande"')
def click_go_to_cart(browser):
    go_to_cart_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/div[2]/div/div[3]/div/div/span/span/a"))
    )
    try:
        browser.execute_script("arguments[0].click();", go_to_cart_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click the 'Aller au panier' button")

@when('I click on "Supprimer" from the cart page')
def click_remove_from_cart(browser):
    remove_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[3]/div[5]/div/div[2]/div/div/form/div[2]/div[3]/div[4]/div/div[2]/div/span[2]/span/input"))
    )
    try:
        browser.execute_script("arguments[0].click();", remove_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click the 'Supprimer' button")

@then('the cart should be empty')
def verify_cart_is_empty(browser):
    try:
        time.sleep(3)
        empty_cart_message = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Votre panier Amazon est vide.')]"))
        )
        assert empty_cart_message.is_displayed(), "The cart is not empty"
    except Exception as e:
        pytest.fail(f"Failed to verify that the cart is empty: {str(e)}")
