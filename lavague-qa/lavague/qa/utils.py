import re
from lavague.core.utilities.pricing_util import build_summary_table


INDENT = "    "
INDENT_PASS = INDENT + "pass"


def remove_comments(code):
    return "\n".join(
        [line for line in code.split("\n") if not line.strip().startswith("#")]
    )


def clean_llm_output(code: str) -> str:
    return code.replace("```python", "").replace("```", "").replace("```\n", "")


def build_run_summary(logs, final_feature_path, final_pytest_path, execution_time):
    token_summary = {
        "world_model_input_tokens": 0,
        "world_model_output_tokens": 0,
        "action_engine_input_tokens": 0,
        "action_engine_output_tokens": 0,
        "total_world_model_tokens": 0,
        "total_action_engine_tokens": 0,
        "total_embedding_tokens": 0,
        "total_world_model_cost": 0.0,
        "total_action_engine_cost": 0.0,
        "total_embedding_cost": 0.0,
        "total_step_tokens": 0,
        "total_step_cost": 0.0,
    }
    for key in token_summary.keys():
        if key in logs.columns:
            token_summary[key] += logs[key].sum()

    summary = ""
    summary += f"\nFinished generating tests in {execution_time:.1f}s\n\n"
    summary += f"   Feature file: {final_feature_path}\n"
    summary += f"   Pytest file:  {final_pytest_path}\n"
    # turn off TokenCounter output as it counts only the LaVague run and not the pytest generation
    # summary += build_summary_table(token_summary, verbose=False)

    summary += f"\nRun the following command to execute your tests:\n\n   pytest {final_pytest_path}\n"

    return summary


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
