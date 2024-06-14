import argparse
import os
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver

TEMP_FILES_DIR = "./generated_files"
TESTS_DIR = "./tests"


def main(url, feature_file):
    feature_name, feature_file_name, scenarios = parse_feature_file(feature_file)

    for scenario in scenarios:
        try:
            nodes, screenshot, selenium_code = run_test_case(url, scenario)
            code = generate_temp_code(
                url, feature_name, scenario, selenium_code, nodes, screenshot
            )
            write_temp_file(feature_name, scenario["name"], code)
        except Exception as e:
            print(f"-- Failed to process test case {scenario['name']}: {e}")

    merge_and_write_final_code(
        feature_file, feature_name, feature_file_name, len(scenarios)
    )


def parse_feature_file(file_path):
    feature_file_name = os.path.basename(file_path)
    feature_name = feature_file_name.split(".")[0]
    with open(file_path, "r") as file:
        file_contents = file.read()

    scenarios = file_contents.split("Scenario:")
    parsed_scenarios = []
    for scenario in scenarios[1:]:
        scenario_name, *scenario_steps = scenario.strip().split("\n")
        parsed_scenarios.append(
            {
                "name": scenario_name.strip(),
                "steps": [step.strip() for step in scenario_steps],
            }
        )

    print(f"-- Parsed feature file: {feature_file_name}")
    return feature_name, feature_file_name, parsed_scenarios


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


def get_latest_screenshot_path(directory):
    files = os.listdir(directory)
    full_paths = [os.path.join(directory, f) for f in files]
    return max(full_paths, key=os.path.getmtime)


def pil_image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


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
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            },
        ],
    )
    code = completion.choices[0].message.content.strip()
    return code.replace("```python", "").replace("```", "").replace("```\n", "")


def write_temp_file(feature_name, scenario_name, code):
    if not os.path.exists(TEMP_FILES_DIR):
        os.makedirs(TEMP_FILES_DIR)

    file_path = f"{TEMP_FILES_DIR}/{feature_name}_{scenario_name}.py"
    with open(file_path, "w") as file:
        file.write(code)
    print(f"-- Test case written to {file_path}")


def merge_and_write_final_code(
    feature_file, feature_name, feature_file_name, scenario_count
):
    print(
        f"-- Merging {scenario_count} scenarios into a single file for feature: {feature_file_name}"
    )

    final_code = merge_files(feature_file)
    if not os.path.exists(TESTS_DIR):
        os.makedirs(TESTS_DIR)

    final_file_path = f"{TESTS_DIR}/{feature_name}.py"
    with open(final_file_path, "w") as file:
        file.write(final_code)
    print(f"-- Final test cases written to {final_file_path}")


def merge_files(feature_file_path):
    with open(feature_file_path, "r") as file:
        feature_file_content = file.read()

    file_paths = [
        os.path.join(TEMP_FILES_DIR, file)
        for file in os.listdir(TEMP_FILES_DIR)
        if file.endswith(".py")
    ]
    base_prompt = f"Merge the following pytest-bdd files into a single file with unique steps for the following feature, only output python code and nothing else:\n\nfeature file:\n\n{feature_file_content}\n\n"

    code_contents = [open(file_path, "r").read() for file_path in file_paths]
    combined_prompt = base_prompt + "\n\n".join(
        f"Code File {i+1}:\n{content}\n\n" for i, content in enumerate(code_contents)
    )

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


def build_prompt(url, feature_file_name, test_case, selenium_code, nodes):
    return f"""Generate a valid pytest-bdd file with the following inputs and examples to guide you:
Base url: {url}\n
Feature file name: {feature_file_name}\n
Test case: {test_case}\n
Already executed code:\n{selenium_code}\n
selected html of the last page: {nodes}\n
Examples:\n\n{EXAMPLES}
"""


SYSTEM_PROMPT = """
You are an expert in software testing frameworks and Python code generation. You answer in python markdown only and nothing else, don't include anything after the last backticks. Your task is to:
1. Process a Gherkin test, existing Selenium code that was ran during the test by an agent, relevant HTML nodes, and the screenshot of the last state of the page.
2. Generate an assert statement for the last condition of the test case.
3. Package everything in a pytest-bdd file following best practices. 
Requirements:
- Use descriptive function names and name the scenario appropriately.
- Use execute_script to handle potential ElementClickInterceptedException during clicks.
- Include fixtures, scenario, Gherkin-style definitions, etc.
- Use try-except blocks to catch exceptions and raise pytest.fail for assert condition steps as needed.
- Do not generate asserts for 'Given', 'When', or 'And' steps; only generate asserts for 'Then' steps.
- Always use provided selenium code that was already executed to find valid selectors for the final pytestfile. 
- You answer in python code only and nothing else.
"""

EXAMPLES = """
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytest_bdd import scenarios, given, when, then
# Constants
BASE_URL = 'https://form.jotform.com/241472287797370'
# Scenarios
scenarios('test_form_submission.feature')
# Fixtures
@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    driver.get(BASE_URL)
    yield driver
    driver.quit()
# Steps
@given('I am on the job application page')
def i_am_on_the_job_application_page(browser):
    pass
@when('I enter "John" in the "First Name" field')
def i_enter_first_name(browser):
    first_name_field = browser.find_element(By.XPATH, "/html/body/form/div[1]/ul/li[2]/div/div/span[1]/input")
    first_name_field.send_keys("John")
@when('I enter "Doe" in the "Last Name" field')
def i_enter_last_name(browser):
    last_name_field = browser.find_element(By.XPATH, "/html/body/form/div[1]/ul/li[2]/div/div/span[2]/input")
    last_name_field.send_keys("Doe")
@when('I enter "john.doe@example.com" in the "Email Address" field')
def i_enter_email_address(browser):
    email_field = browser.find_element(By.XPATH, "/html/body/form/div[1]/ul/li[3]/div/span/input")
    email_field.send_keys("john.doe@example.com")
@when('I enter "(123) 456-7890" in the "Phone Number" field')
def i_enter_phone_number(browser):
    phone_number_field = browser.find_element(By.XPATH, "/html/body/form/div[1]/ul/li[4]/div/span/input")
    phone_number_field.send_keys("(123) 456-7890")
@when('I leave the "Cover Letter" field empty')
def i_leave_cover_letter_empty():
    # No action needed as the field should remain empty
    pass
@when('I click the "Apply" button')
def i_click_apply_button(browser):
    apply_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/form/div[1]/ul/li[6]/div/div/button"))
    )
    browser.execute_script("arguments[0].scrollIntoView(true);", apply_button)
    apply_button.click()
@then('I should see an error message for the "Cover Letter" field')
def i_should_see_error_message(browser):
    try:
        error_message = browser.find_element(By.XPATH, "/html/body/form/div[1]/ul/li[5]/div/div/span")
        assert error_message.is_displayed()
    except Exception as e:
        pytest.fail(f"Error message not displayed: {e}")
"""

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
    parser = argparse.ArgumentParser(
        description="Process a URL and a file path to generate pytest-bdd test cases"
    )
    parser.add_argument(
        "--feature",
        type=str,
        required=True,
        help="The path of the .feature file with your test cases",
    )
    parser.add_argument(
        "--url", type=str, required=True, help="The start URL for your test cases"
    )

    args = parser.parse_args()
    main(args.url, args.feature)
