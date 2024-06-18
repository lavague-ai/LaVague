# QA Automation with LaVague and Pytest

## Use case

LaVague is a great tool to help you write and maintain automated tests more efficiently. Writing test scripts manually is time consuming, using recorders can help but scripts can break if the page structure changes. 

LaVague can generate reusable `pytest-bdd` code from a test case description written in `Gherkin`. If the page changes, simply re-run LaVague to update your test scripts. 

??? note "Example file generated from a Gherkin test case with two scenarios"
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

See our script in action generating automated tests for a e-commerce Cart feature 

<iframe width="100%" height="400" src="https://www.youtube.com/embed/HVVDjYCklBc?si=LNHUYW1zETQK2RMB" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Script usage

You can run this example directly with a [CLI script available here](https://github.com/lavague-ai/LaVague/blob/main/examples/qa-automation/). We provide a sample `.feature` file containing a single use case.

**Install the latest LaVague release**

```bash
pip install lavague
```

!!! tips "Pre-requisites"

    We use OpenAI's models, for the embedding, LLM and Vision model. You will need to set the **OPENAI_API_KEY** variable in your local environment with a valid API key for this example to work.

**Download the script**

```bash
wget https://github.com/lavague-ai/LaVague/blob/main/examples/qa-automation/qa_automation.py
```

**Execute the script**

```bash
python qa_automation.py --url https://www.saucedemo.com/v1/inventory.html --feature tests/test_cart.feature
```

| Parameter                  | Description                                                                                                                                                  |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| url (str)                        | The URL of the website you'd like to generate tests for                                              |
| feature (str)  | The file path of your `.feature` file containing your Gherkin scenarios |

By default, temporary files are generated under `./generated_file` and final test code is created in `./tests`. 

Assuming you use this default configuration, you can simply use `pytest -v tests` to run the generated tests.

You can change those directories by opening the script and changing the following variables: 

```python
TEMP_FILES_DIR = "./generated_files"
TESTS_DIR = "./tests"
```


??? note "Example `pytest-bdd` file generated by this script"
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


## Script walk through

Let's walk through some of the core components of our script to give you a better understanding of how we use LaVague to make you more efficient at testing your web apps. 

### Starting from Gherkin scenarios and an URL

Gherkin is a language used in behavior-driven development (BDD) to describe feature behavior. 

Our example `.feature` file - [available here](https://github.com/lavague-ai/LaVague/blob/main/examples/qa-automation/tests/test_cart.feature) - uses Gherkin and describes a Cart scenario. 

We execute our script on this demo website: https://www.saucedemo.com/v1/inventory.html


```gherkin
Feature: Cart

  Scenario: Add an item to cart
    Given the user is on the home page
    When the user clicks on a product
    And the user is on the product details page
    And the user clicks on 'ADD TO CART'
    And the user clicks on the Cart icon
    Then the user should see the item in the cart
```

### The main loop

Our main logic consists of the following steps:

- parse test cases
- for each scenario: 
    - run the test case with LaVague
    - record page state and generate the assert statement
    - save the code in a temporary folder
- merge all temporary code in a single `pytest-bdd` file

```python
def main(url, feature_file):
    feature_name, feature_file_name, scenarios = parse_feature_file(feature_file)

    for scenario in scenarios:
        try:
            nodes, screenshot, selenium_code = run_test_case(url, scenario)
            code = generate_temp_code(url, feature_name, scenario, selenium_code, nodes, screenshot)
            write_temp_file(feature_name, scenario['name'], code)
        except Exception as e:
            print(f"-- Failed to process test case {scenario['name']}: {e}")

    merge_and_write_final_code(feature_file, feature_name, feature_file_name, len(scenarios))
```

### Running a test case with a LaVague agent

In order to record all information needed to generate a robust test case, we run each scenario with LaVague.

```python
def run_test_case(url, scenario):
    test_case = "\n".join(scenario["steps"])

    selenium_driver = SeleniumDriver(headless=False)
    world_model = WorldModel()
    action_engine = ActionEngine(selenium_driver)
    agent = WebAgent(world_model, action_engine)
    objective = f"Run this test case: \n\n{test_case}"

    print(f"-- Running test case: {scenario['name']}")

    agent.get(url)
    agent.run(objective)

    nodes = action_engine.navigation_engine.get_nodes(
        f"We have ran the test case, generate the final assert statement.\n\ntest case:\n{test_case}"
    )

    logs = agent.logger.return_pandas()
    last_screenshot_path = get_latest_screenshot_path(logs.iloc[-1]["screenshots_path"])
    b64_img = pil_image_to_base64(last_screenshot_path)
    selenium_code = "\n".join(logs["code"].dropna())

    agent.driver.driver.close()

    return nodes, b64_img, selenium_code
```

Here are the core setup components of this function: 
- Create a `SeleniumDriver` (browser interaction), a `WorldModel` (uses vision and LLMs for reasoning)
- Create a `WebAgent` with those two components.
- Load the URL using `agent.get(url)`

Then, we provide a natural language instruction to our agent and start the agent. 
```python
objective = f"Run this test case: \n\n{test_case}"
agent.run(objective)
```

### Recording page state

The agent reasons, generates Selenium code and executes it until it finishes running the test. Once the agent has stopped, we extract relevant info what the agent recorded. 


First we perform Retrieval-Augmented Generation on the last state of the page by asking our retriever for the most relevant nodes to generate the assert statement.

```python
nodes = action_engine.navigation_engine.get_nodes(
        f"We have ran the test case, generate the final assert statement.\n\ntest case:\n{test_case}"
    )
```

By doing this we avoid passing the entire HTML page to a LLM query. 

Then, from the logs, we get the last generated screenshot representing the final state of the page and we encode it to base 64 (necessary to call the OpenAI API later).

```python
    logs = agent.logger.return_pandas()
    last_screenshot_path = get_latest_screenshot_path(logs.iloc[-1]["screenshots_path"])
    b64_img = pil_image_to_base64(last_screenshot_path)
```

We also extract all the Selenium code that was executed during the run. This provides a source of selectors already validated by LaVague (effectively replacing a traditional recorder). 

```python
    selenium_code = "\n".join(logs["code"].dropna())
```

### Generating a temporary file

To handle multiple scenarios, we generate temporary files that we will merge later. We simply do a request to the GPT-4o API and ask it to generate a pytest file from all the information we recorded (html nodes, screenshot, selenium code).

```python
def generate_temp_code(url, feature_name, test_case, selenium_code, nodes, b64_img):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    prompt = build_prompt(url, feature_name, test_case, selenium_code, nodes)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
                ],
            },
        ],
    )
    code = completion.choices[0].message.content.strip()
    return code.replace("```python", "").replace("```", "").replace("```\n", "")
```

### Merging all temporary code in a single file

We want to keep a one-to-one relationship between a `.feature` file and a `.py` file. 

To generate a single file that can handle all test statements in the original feature file, we will use the GPT-4o API to merge all the individual scenario code. 

```python
def merge_files(feature_file_path):
    with open(feature_file_path, "r") as file:
        feature_file_content = file.read()

    file_paths = [os.path.join(TEMP_FILES_DIR, file) for file in os.listdir(TEMP_FILES_DIR) if file.endswith('.py')]
    
    base_prompt = f"Merge the following pytest-bdd files into a single file with unique steps for the following feature, only output python code and nothing else:\n\nfeature file:\n\n{feature_file_content}\n\n"

    code_contents = [open(file_path, 'r').read() for file_path in file_paths]
    combined_prompt = base_prompt + "\n\n".join(f"Code File {i+1}:\n{content}\n\n" for i, content in enumerate(code_contents))

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [{"type": "text", "text": combined_prompt}]},
        ],
    )
    code = completion.choices[0].message.content.strip()
    return code.replace("```python", "").replace("```", "").replace("```\n", "")
```

The function above simply concatenates all code files in our temporary directory and prompts GPT-4o to merge them all in a single file following best practices. 

By default, this final file will be generated in `./tests`. 


## Running our tests

Assuming you use this default configuration, you can simply use `pytest -v tests` to run the generated tests.

## Limitations and next steps

!!! warning "Verify the code"

    100% accuracy is not guaranteed and we advise you review the generated final code file

**Main limitation**: LaVague can struggle on very complex and/or JavaScript heavy websites mostly because the difficulty of identifying the right selector.

**Ideas for going further**:

- Add support for other testing frameworks
- Generate Gherkin file from JIRA tickets
- Integrate LaVague in the life cycle of your tests

## Need help ? Found a bug ?
Join our [Discord](https://discord.gg/invite/SDxn9KpqX9) to reach our core team and get support!
