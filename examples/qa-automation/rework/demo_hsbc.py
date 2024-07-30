
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time

# Constants
BASE_URL = 'https://www.hsbc.fr/'

# Scenarios
scenarios('demo_hsbc.feature')

# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# Steps
@given('the user is on the HSBC homepage')
def go_to_homepage(browser):
    browser.get(BASE_URL)

@when('the user clicks on "Tout accepter" to accept cookies')
def accept_cookies(browser):
    accept_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/div[3]/button[2]"))
    )
    try:
        browser.execute_script("arguments[0].click();", accept_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to accept cookies")

@when('the user clicks on "Global Banking and Markets"')
def click_global_banking(browser):
    global_banking_link = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/main/div[2]/div/div/div/div/div[4]/div/div/div/div/div/div/div[2]/div/a"))
    )
    try:
        browser.execute_script("arguments[0].click();", global_banking_link)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click on Global Banking and Markets")

@when('the user clicks on "Je comprends, continuons"')
def click_continue(browser):
    continue_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div/div/a[2]"))
    )
    try:
        browser.execute_script("arguments[0].click();", continue_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click on Je comprends, continuons")

@when('the user navigates to the new tab opened')
def switch_to_new_tab(browser):
    time.sleep(3)
    browser.switch_to.window(browser.window_handles[1])

@when('the user clicks on "Accept all cookies"')
def accept_all_cookies(browser):
    accept_all_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div/div[2]/button[2]"))
    )
    try:
        browser.execute_script("arguments[0].click();", accept_all_button)
    except ElementClickInterceptedException:
        pytest.fail("Failed to accept all cookies")

@when('the user clicks on "About us"')
def click_about_us(browser):
    about_us_link = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div/div/div/nav/div/ul/li[4]/a"))
    )
    try:
        browser.execute_script("arguments[0].click();", about_us_link)
    except ElementClickInterceptedException:
        pytest.fail("Failed to click on About us")

@then('the user should be on the "About us" page of the "Global Banking and Markets" services of HSBC')
def verify_about_us_page(browser):
    try:
        WebDriverWait(browser, 10).until(
            EC.title_contains("About Global Banking and Markets | HSBC")
        )
    except Exception as e:
        pytest.fail(f"Failed to verify About us page: {str(e)}")
