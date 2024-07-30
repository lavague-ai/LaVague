
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time

# Constants
BASE_URL = 'https://fr.wikipedia.org/'

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
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[3]/div/form/div/div[2]/div/input"))
    )
    username_field.send_keys(username)

@when(parsers.parse('the user enters {password} in the password field'))
def enter_password(browser, password):
    password_field = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[3]/div/form/div[2]/div[2]/div/input"))
    )
    password_field.send_keys(password)

@when('the user submits the login form')
def submit_login_form(browser):
    login_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[3]/div/form/div[4]/div/button"))
    )
    try:
        browser.execute_script("arguments[0].click();", login_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to submit the login form")

@then('the login should be successful and the user is redirected to the main page')
def verify_login_success(browser):
    try:
        user_page_link = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@id='pt-userpage']//a[contains(@href, 'Lavague-test')]"))
        )
        assert user_page_link is not None, "User page link not found, login might have failed"
    except Exception as e:
        pytest.fail(f"Failed to verify login success: {str(e)}")
