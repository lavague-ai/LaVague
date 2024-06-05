from pathlib import Path
from typing import Callable, Optional
from playwright.sync_api import Page
from lavague.core.base_driver import BaseDriver


class PlaywrightDriver(BaseDriver):
    driver: Page

    def __init__(
        self,
        url: Optional[str] = None,
        get_sync_playwright_page: Optional[Callable[[], Page]] = None,
    ):
        super().__init__(url, get_sync_playwright_page)

    def default_init_code(self) -> Page:
        # these imports are necessary as they will be pasted to the output
        try:
            from playwright.sync_api import sync_playwright
        except (ImportError, ModuleNotFoundError) as error:
            raise ImportError(
                "Please install playwright using `pip install playwright` and then `playwright install` to install the necessary browser drivers"
            ) from error
        p = sync_playwright().__enter__()
        browser = p.chromium.launch()
        page = browser.new_page()
        return page

    def get_driver(self) -> Page:
        return self.driver

    def get_current_screenshot_folder(self) -> Path:
        pass

    def get_screenshot_as_png(self) -> bytes:
        pass

    def resize_driver(self, width, height) -> None:
        self.driver.set_viewport_size({"width": width, "height": height})

    def get_url(self) -> Optional[str]:
        if self.driver.url == "about:blank":
            return None
        return self.driver.url

    def go_to_url_code(self, url: str) -> str:
        return f'page.goto("{url}")'

    def goto(self, url: str) -> None:
        return self.driver.goto(url)

    def get_html(self) -> str:
        return self.driver.content()

    def get_obs(self) -> dict:
        # TODO
        return {}

    def save_screenshot(self, filename: str) -> None:
        return self.driver.screenshot(path=filename)

    def get_dummy_code(self) -> str:
        return "page.mouse.wheel(delta_x=0, delta_y=500)"

    def destroy(self) -> None:
        self.driver.close()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.driver.locator(f"xpath={xpath}").is_visible()
        except:
            return False

    def exec_code(self, code: str):
        exec(self.import_lines)
        page = self.driver
        exec(code)

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
