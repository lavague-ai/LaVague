import re

INDENT = "    "
INDENT_PASS = INDENT + "pass"


def remove_comments(code):
    return "\n".join(
        [line for line in code.split("\n") if not line.strip().startswith("#")]
    )


def clean_llm_output(code: str) -> str:
    return code.replace("```python", "").replace("```", "").replace("```\n", "")


# all utils below are used for building the pytest file without LLMs
def to_snake_case(s: str):
    s = s.lower()
    s = re.sub(r"[^\w\s]", "_", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"__+", "_", s)
    return s.strip("_")


def get_nav_action_code(action):
    action_name = action["name"]
    args = action["args"]
    xpath = None if args is None else args.get("xpath")

    if action_name == "click":
        return get_click_action(xpath)
    elif action_name == "setValue":
        return get_set_value_action(xpath, args["value"])
    elif action_name == "setValueAndEnter":
        return get_set_value_action(xpath, args["value"], True)
    elif action_name == "dropdownSelect":
        return get_select_action(xpath, args["value"])

    return "pass"


def get_nav_control_code(instruction):
    if "SCROLL_DOWN" in instruction:
        return "browser.scroll_down()"
    if "SCROLL_UP" in instruction:
        return "browser.scroll_up()"
    if "WAIT" in instruction:
        return "import time\n    time.sleep(5)"
    if "BACK" in instruction:
        return "browser.back()"
    if "SCAN" in instruction:
        return "pass"
    if "MAXIMIZE_WINDOW" in instruction:
        return "browser.maximize_window()"
    if "SWITCH_TAB" in instruction:
        tab_id = int(instruction.split(" ")[1])
        return f"browser.switch_tab(tab_id={tab_id})"


def get_click_action(xpath: str):
    return f"""element = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, '{xpath}'))
    )
    browser.execute_script('arguments[0].click();', element)
"""


def get_select_action(xpath, value):
    return f"""element = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, '{xpath}'))
    )
    select = Select(element)
    try:
        select.select_by_value('{value}')
    except:
        select.select_by_visible_text('{value}')
"""


def get_set_value_action(xpath, value, enter=False):
    code = get_click_action(xpath)
    code += INDENT + f"element.clear()"
    code += "\n" + INDENT + f"element.send_keys('{value}')"
    if enter:
        code += "\n" + INDENT + f"element.send_keys('\ue007')"
    return code
