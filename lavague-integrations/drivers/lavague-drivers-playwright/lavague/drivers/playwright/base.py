from io import BytesIO
import os
from PIL import Image
from typing import Callable, Optional, Any, Mapping
from lavague.core.utilities.format_utils import (
    extract_code_from_funct,
    keep_assignments,
    return_assigned_variables,
)
from playwright.sync_api import Page, Locator
from lavague.core.base_driver import BaseDriver


class PlaywrightDriver(BaseDriver):
    page: Page

    def __init__(
        self,
        url: Optional[str] = None,
        get_sync_playwright_page: Optional[Callable[[], Page]] = None,
        headless: bool = True,
        width: int = 1080,
        height: int = 1080,
        user_data_dir: Optional[str] = None,
    ):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = (
            "1"  # Allow playwright to take a screenshots even if the fonts won't load in head mode.
        )
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.width = 1080
        self.height = 1080
        super().__init__(url, get_sync_playwright_page)

    # Before modifying this function, check if your changes are compatible with code_for_init which parses this code
    # these imports are necessary as they will be pasted to the output
    def default_init_code(self) -> Page:
        try:
            from playwright.sync_api import sync_playwright
        except (ImportError, ModuleNotFoundError) as error:
            raise ImportError(
                "Please install playwright using `pip install playwright` and then `playwright install chromium` to install the necessary browser drivers"
            ) from error
        p = sync_playwright().__enter__()
        if self.user_data_dir is None:
            browser = p.chromium.launch(headless=self.headless)
        else:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir, headless=self.headless
            )
        page = browser.new_page()
        self.page = page
        self.resize_driver(self.width, self.height)
        return self.page

    def code_for_init(self) -> str:
        init_lines = extract_code_from_funct(self.init_function)
        code_lines = [
            "from playwright.sync_api import sync_playwright",
            "",
        ]
        ignore_next = 0
        keep_else = False
        start = False
        for line in init_lines:
            if "__enter__()" in line:
                start = True
            elif not start:
                continue
            if "self.headless" in line:
                line = line.replace("self.headless", str(self.headless))
            if "self.user_data_dir" in line:
                line = line.replace("self.user_data_dir", f'"{self.user_data_dir}"')
            if "if" in line:
                if self.user_data_dir is not None:
                    ignore_next = 1
                    keep_else = True
            elif "else" in line:
                if not keep_else:
                    ignore_next = 3
            elif ignore_next <= 0:
                if "self" not in line:
                    code_lines.append(line.strip())
            else:
                ignore_next -= 1
        code_lines.append(self.code_for_resize(self.width, self.height))
        return "\n".join(code_lines) + "\n"

    def get_driver(self) -> Page:
        return self.page

    def get_screenshot_as_png(self) -> bytes:
        return self.page.screenshot(animations="disabled")

    def resize_driver(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.page.set_viewport_size({"width": width, "height": height})

    def code_for_resize(self, width, height) -> str:
        return f'page.set_viewport_size({{"width": {width}, "height": {height}}})'

    def get_url(self) -> Optional[str]:
        if self.page.url == "about:blank":
            return None
        return self.page.url

    def code_for_get(self, url: str) -> str:
        return f'page.goto("{url}")'

    def get(self, url: str) -> None:
        return self.page.goto(url)

    def back(self) -> None:
        return self.page.go_back()

    def code_for_back(self) -> None:
        return "page.go_back()"

    def get_html(self) -> str:
        return self.page.content()

    def destroy(self) -> None:
        self.page.close()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.page.locator(f"xpath={xpath}").is_visible()
        except:
            return False

    def get_highlighted_element(self, generated_code: str):
        local_scope = {"page": self.get_driver()}
        assignment_code = keep_assignments(generated_code)
        self.exec_code(assignment_code, locals=local_scope)
        variable_names = return_assigned_variables(generated_code)
        elements = []
        for variable_name in variable_names:
            var = local_scope[variable_name]
            if type(var) == Locator:
                elements.append(var)
        if len(elements) == 0:
            raise ValueError(f"No element found.")

        outputs = []
        for element in elements:
            element: Locator

            bounding_box = {}
            viewport_size = {}

            self.execute_script(
                "arguments[0].setAttribute('style', arguments[1]);",
                element,
                "border: 2px solid red;",
            )
            self.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", element
            )
            screenshot = self.get_screenshot_as_png()

            bounding_box["x1"] = element.bounding_box()["x"]
            bounding_box["y1"] = element.bounding_box()["y"]
            bounding_box["x2"] = bounding_box["x1"] + element.bounding_box()["width"]
            bounding_box["y2"] = bounding_box["y1"] + element.bounding_box()["height"]

            viewport_size["width"] = self.execute_script("return window.innerWidth;")
            viewport_size["height"] = self.execute_script("return window.innerHeight;")
            screenshot = BytesIO(screenshot)
            screenshot = Image.open(screenshot)
            output = {
                "screenshot": screenshot,
                "bounding_box": bounding_box,
                "viewport_size": viewport_size,
            }
            outputs.append(output)
        return outputs

    def exec_code(
        self,
        code: str,
        globals: dict[str, Any] = None,
        locals: Mapping[str, object] = None,
    ):
        exec(self.import_lines)
        page = self.page
        exec(code, globals, locals)

    def execute_script(self, js_code: str, *args) -> Any:
        args = list(arg for arg in args)
        for i, arg in enumerate(args):
            if type(arg) == Locator:
                args[i] = arg.element_handle()  # playwright only accept element_handles
        script = f"(arguments) => {{{js_code}}}"
        return self.page.evaluate(script, args)

    def code_for_execute_script(self, js_code: str, *args) -> str:
        return f"page.evaluate(\"(arguments) => {{{js_code}}}\", [{', '.join(str(arg) for arg in args)}])"

    def get_capability(self) -> str:
        return """
Your goal is to write Playwright Python code to answer queries.

Your answer must be a Python markdown only.
You can have access to external websites and libraries.

In your playwright code, you should only use the page.locator() or page.get_by_text() methods to uniquely locate and interact with the elements on the page. 
For page.locator(), you must use XPath selectors to uniquely locate elements.
you must always interact with the first matching element by calling .first and performing an action on it (e.g., click, fill, type, etc.).

You can assume the following code has been executed:
```python
from playwright.sync_api import sync_playwright
p = playwright().__enter__()
browser = p.chromium.launch()
page = browser.new_page()
```

---

HTML:
<!DOCTYPE html>
<html>
<head>
    <title>Mock Search Page</title>
</head>
<body>
    <h1>Search Page Example</h1>
    <input id="searchBar" type="text" placeholder="Type here to search...">
    <button id="searchButton">Search</button>
</body>
</html>

Query: Click on the search bar 'Type here to search...', type 'playwright', and press the 'Enter' key

Completion:
```python
# Let's proceed step by step.
# First we need to identify the component first, then we can click on it.

# Based on the HTML, the link can be uniquely identified using the ID "searchBar"
# Get the first matching element and click on it
search_bar_button = page.locator("//input[@id='searchBar']").first
search_bar_button.click()

# Type 'playwright' into the search bar
search_bar_button.fill('playwright')

# Press the 'Enter' key
search_bar_button.press('Enter')

```

---

HTML:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mock Page for Playwright</title>
</head>
<body>
    <h1>Welcome to the Mock Page</h1>
    <div id="links">
        <a href="#link1" id="link1">Link 1</a>
        <br>
        <a href="#link2" class="link">Link 2</a>
        <br>
    </div>
</body>
</html>

Query: Click on the title Link 1 and then click on the title Link 2

Completion:
```python
# Let's proceed step by step.
# First we need to identify the first component, then we can click on it. Then we can identify the second component and click on it.

# Based on the HTML, the first link the link can be uniquely identified using the text "Link 1"
# Let's use get_by_text to identify the link and get the first matching element
link1 = page.get_by_text('Link 1').first

# Then we click on the link
link1.click()

# The other link can be uniquely identified using the text Link 2
# Let's use get_by_text to identify the link and get the first matching element
link2 = page.get_by_text('Link 2').first

# Click on the element found
link2.click()
```

---

HTML:
<!DOCTYPE html>
<html>
<head>
    <title>Mock Page</title>
</head>
<body>
    <p id="para1">This is the first paragraph.</p>
    <p id="para2">This is the second paragraph.</p>
    <p id="para3">This is the third paragraph, which we will select and copy.</p>
    <p id="para4">This is the fourth paragraph.</p>
</body>
</html>

Query: Select the text inside the third paragraph

Completion:
```python
# Let's proceed step by step.

# Locate the third paragraph using the ID "para3" and get the first matching element
third_paragraph = page.locator("//p[@id='para3']").first

# Select the text inside the third paragraph
third_paragraph.select_text()
```

---

HTML:

Query: Scroll up a bit

Completion:
```python
# Let's proceed step by step.
# We don't need to use the HTML data as this is a stateless operation.
# 200 pixels should be sufficient. Let's execute the JavaScript to scroll up.

page.evaluate("window.scrollBy(0, 200)")
```

---

---

HTML:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enhanced Mock Page for Playwright Testing</title>
</head>
<body>
    <h1>Enhanced Test Page for Playwright</h1>
    <div class="container">
        <button id="firstButton" onclick="alert('First button clicked!');">First Button</button>
        <!-- This is the button we're targeting with the class name "action-btn" -->
        <button class="action-btn" onclick="alert('Action button clicked!');">Action Button</button>
        <div class="nested-container">
            <button id="testButton" onclick="alert('Test Button clicked!');">Test Button</button>
        </div>
        <button class="hidden" onclick="alert('Hidden button clicked!');">Hidden Button</button>
    </div>
</body>
</html>


Query: Click on the Button 'Action Button'

Completion:
```python
# Let's proceed step by step.
# First we need to identify the button first, then we can click on it.

# Based on the HTML provided, we need to devise the best strategy to select the button and get the first matching element.
# The action button can be identified using the text "Action Button"
action_button = page.get_by_text("Action Button").first

# Then we can click on it
action_button.click()
```

---
"""
