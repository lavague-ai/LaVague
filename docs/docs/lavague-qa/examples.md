# LaVague QA Examples

!!! warning "Beta release"
    LaVague QA is still a work in progress and may contain bugs. Join our [community of amazing contributors](https://discord.gg/invite/SDxn9KpqX9) to help make this tool more reliable!

We will periodically add [examples in our repository](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/). In this section, we will go over each of the Gherkin files and showcase the generated code.

All commands shown in this documentation assume you're running them from the LaVague repository in order to use the provided examples. 


| URL                              | Link to file                                                  | Purpose                                                  |
|:---------------------------------|:--------------------------------------------------------------|:---------------------------------------------------------|
| https://amazon.fr/               | [demo_amazon.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/demo_amazon.feature)       | Tests the Amazon search, cart and cart deletion to ensure expected behavior |
| https://laposte.fr/              | [demo_laposte.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/demo_laposte.feature)     | Tests an interactive shipping cost calculator to ensure expected output |
| https://en.wikipedia.org/        | [demo_wikipedia.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/demo_wikipedia.feature) | Tests the login feature of Wikipedia  |
| https://hsbc.fr/                 | [demo_hsbc.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague-qa/features/demo_hsbc.feature)           | Tests proper multi-tab navigation and cookie banners |


In each of these examples, we'll showcase how LaVague QA can be used to generate tests for critical parts of your websites.

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/LaVague/blob/main/lavague-qa/demo_lavague_QA.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a>

## Amazon Cart testing

In this example, we test that the feature to remove items from our cart on Amazon.

### Feature file

```gherkin
Feature: Cart

  Scenario: Add and remove a single product from cart
    Given the user is on the homepage
    When the user clicks on "Accepter" to accept cookies
    And the user enters "Zero to One" into the search bar and press Enter
    And the user clicks on the first product in the search results
    And the user clicks on the "Ajouter au panier" button
    And the confirmation message is displayed
    And the user clicks on "Aller au panier" under "Passer la commande"
    And the user clicks on "Supprimer" from the cart page
    Then the cart should be empty
```

## Generate pytest

```sh
lavague-qa --url https://amazon.fr/ --feature lavague-qa/features/demo_amazon.feature
```

??? note "Generated code"
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


## Interactive shipping calculator testing

In this example, we test the interactive elements of a shipping cost calculator to ensure they return the expected output.

### Feature file

```gherkin
Feature: Shipping cost calculator

  Scenario: Estimate shipping costs for a large package
    Given the user is on the homepage
    When the user clicks on "J'accepte" to accept cookies
    And the user clicks on "Envoyer un colis"
    And the user clicks on the "Format du colis" dropdown under "Dimension"
    And the user clicks on "Volumineux & tube" from the dropdown results
    And the user enters 15 in the "Poids" field
    And the user waist for the cost to update
    Then the cost should be "34,70 €"
```

## Generate pytest

```sh
lavague-qa --url https://laposte.fr/ --feature lavague-qa/features/demo_laposte.feature
```

??? note "Generated code"  
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
    BASE_URL = 'https://www.laposte.fr/'

    # Scenarios
    scenarios('demo_laposte.feature')

    # Fixtures
    @pytest.fixture
    def browser():
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    # Steps
    @given('the user is on the homepage')
    def user_on_homepage(browser):
        browser.get(BASE_URL)

    @when('the user clicks on "J\'accepte" to accept cookies')
    def accept_cookies(browser):
        accept_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div[2]/button"))
        )
        accept_button.click()

    @when('the user clicks on "Envoyer un colis"')
    def click_envoyer_colis(browser):
        envoyer_colis_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div[2]/div/main/div/div[2]/div[4]/div/div/a[3]"))
        )
        envoyer_colis_button.click()

    @when('the user clicks on the "Format du colis" dropdown under "Dimension"')
    def click_format_dropdown(browser):
        format_dropdown = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/main/div/div[2]/div[2]/div/div/div/div/div/div/div/div[3]/div[2]/fieldset/div"))
        )
        format_dropdown.click()

    @when('the user clicks on "Volumineux & tube" from the dropdown results')
    def select_volumineux_tube(browser):
        volumineux_tube_option = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/main/div/div[2]/div[2]/div/div/div/div/div/div/div/div[3]/div[2]/fieldset/div[2]/div/label[2]"))
        )
        volumineux_tube_option.click()

    @when('the user enters 15 in the "Poids" field')
    def enter_weight(browser):
        weight_field = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div/div/main/div/div[2]/div[2]/div/div/div/div/div/div/div/div[4]/div[2]/div/div/div/div/input"))
        )
        weight_field.clear()
        weight_field.send_keys("15")

    @when('the user waits for the cost to update')
    def wait_for_cost_update(browser):
        time.sleep(3)

    @then('the cost should be "34,70 €"')
    def verify_cost(browser):
        cost_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='calculator__cta__price']"))
        )
        assert cost_element.text == "34,70 €", f"Expected cost to be '34,70 €', but got '{cost_element.text}'"
    ```


## Wikipedia login testing


### Feature file

Here, we test the login functionality on Wilkipedia by providing credentials. 

```gherkin
Feature: Wikipedia Login

  Scenario: User logs in successfully
    Given the user is on the Wikipedia homepage
    When the user navigates to the login page
    And the user enters Lavague-test in the username field
    And the user enters lavaguetest123 in the password field
    And the user clicks on login under the username and password field
    Then the login is successful and the user is redirected to the main page
```

## Generate pytest

```sh
lavague-qa --url https://en.wikipedia.org/ --feature lavague-qa/features/demo_wikipedia.feature
```

??? note "Generated code"
        ```py
        import pytest
        from pytest_bdd import scenarios, given, when, then
        from selenium.webdriver.chrome.webdriver import WebDriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

        # Constants
        BASE_URL = 'https://en.wikipedia.org/'

        # Scenarios
        scenarios('demo_wikipedia.feature')

        # Fixtures
        @pytest.fixture
        def browser():
            driver = WebDriver()
            driver.implicitly_wait(10)
            yield driver
            driver.quit()

        # Steps

        @given('the user is on the Wikipedia homepage')
        def the_user_is_on_the_wikipedia_homepage(browser: WebDriver):
            browser.get(BASE_URL)

        @when('the user navigates to the login page')
        def the_user_navigates_to_the_login_page(browser: WebDriver):
            element = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/header/div[2]/nav/div/div[4]/div/ul/li[2]/a'))
            )
            browser.execute_script('arguments[0].click();', element)

            
        @when('the user enters Lavague-test in the username field')
        def the_user_enters_lavague_test_in_the_username_field(browser: WebDriver):
            element = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div/div[2]/div/input'))
            )
            browser.execute_script('arguments[0].click();', element)
            element.clear()
            element.send_keys('Lavague-test')
            
        @when('the user enters lavaguetest123 in the password field')
        def the_user_enters_lavaguetest123_in_the_password_field(browser: WebDriver):
            element = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div[2]/div[2]/div/input'))
            )
            browser.execute_script('arguments[0].click();', element)
            element.clear()
            element.send_keys('lavaguetest123')
            
        @when('the user clicks on login under the username and password field')
        def the_user_clicks_on_login_under_the_username_and_password_field(browser: WebDriver):
            element = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]/div/form/div[4]/div/button'))
            )
            browser.execute_script('arguments[0].click();', element)

            
        @then('the login is successful and the user is redirected to the main page')
        def the_login_is_successful_and_the_user_is_redirected_to_the_main_page(browser: WebDriver):
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            
            user_element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//li[@id='pt-userpage']//span"))
            )
            assert user_element.text.strip() == "Lavague-test"
    ```

## Test cookies and redirections work as expected

Here we test the cookie banners and some basic navigation on the HSBC website. 

### Feature file

```gherkin
Feature: HSBC navigation

  Scenario: Multi tab navigation
    Given the user is on the HSBC homepage
    When the user clicks on "Tout accepter" to accept cookies
    And the user clicks on "Global Banking and Markets"
    And the user clicks on "Je comprends, continuons"
    And the user navigates to the new tab opened
    And the user clicks on "Accept all cookies"
    And the user clicks on "About us"
    Then the user should be on the "About us" page of the "Global Banking and Markets" services of HSBC
```

## Generate pytest

```sh
lavague-qa --full-llm --url https://hsbc.fr/ --feature lavague-qa/features/demo_hsbc.feature 
```

For this example, we run with the `-full-llm` flag to generate the pytest since multitab doesn't work with our step by step pytest builder yet. 

??? note "Generated code"
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
    def switch_tab(browser):
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
            pytest.fail("Failed to verify About us page: " + str(e))

    ```

## Learn more

Join our [Discord](https://discord.gg/invite/SDxn9KpqX9) to reach our core team and get support!
