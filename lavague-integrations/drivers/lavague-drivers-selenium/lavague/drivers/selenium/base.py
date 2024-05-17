from typing import Any, Optional, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from lavague.core.base_driver import BaseDriver
from PIL import Image
from lavague.core.utilities.format_utils import (
    return_assigned_variables,
    keep_assignments,
)


class SeleniumDriver(BaseDriver):
    driver: WebDriver

    def __init__(
        self,
        url: Optional[str] = None,
        get_selenium_driver: Optional[Callable[[], WebDriver]] = None,
        headless: bool = True,
        chrome_user_dir: Optional[str] = None,
    ):
        self.headless = headless
        self.chrome_user_dir = chrome_user_dir
        super().__init__(url, get_selenium_driver)

    def default_init_code(self) -> Any:
        # these imports are necessary as they will be pasted to the output
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        if self.chrome_user_dir:
            chrome_options.add_argument(f"--user-data-dir={self.chrome_user_dir}")
        chrome_options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.resize_driver(1024, 1024)
        return self.driver

    def get_driver(self) -> WebDriver:
        return self.driver

    def resize_driver(self, width, height) -> None:
        # Selenium is only being able to set window size and not viewport size
        self.driver.set_window_size(width, height)
        viewport_height = self.driver.execute_script("return window.innerHeight;")

        height_difference = height - viewport_height
        self.driver.set_window_size(width, height + height_difference)

    def get_url(self) -> Optional[str]:
        if self.driver.current_url == "data:,":
            return None
        return self.driver.current_url

    def go_to_url_code(self, url: str) -> str:
        return f'driver.get("{url}")'

    def goto(self, url: str) -> None:
        self.driver.get(url)

    def get_html(self) -> str:
        return self.driver.page_source

    def save_screenshot(self, filename: str) -> None:
        self.driver.save_screenshot(filename)

    def get_dummy_code(self) -> str:
        return 'driver.execute_script("window.scrollBy(0, 500)")'

    def destroy(self) -> None:
        self.driver.quit()

    def check_visibility(self, xpath: str) -> bool:
        try:
            return self.driver.find_element(By.XPATH, xpath).is_displayed()
        except:
            return False

    def exec_code(self, code: str):
        exec(self.import_lines)
        driver = self.driver
        exec(code)

    def resize_driver(self, width, targeted_height):
        """Resize the Selenium driver viewport to a targeted height and width.
        This is due to Selenium only being able to set window size and not viewport size.
        """
        self.driver.set_window_size(width, targeted_height)

        viewport_height = self.driver.execute_script("return window.innerHeight;")

        height_difference = targeted_height - viewport_height
        self.driver.set_window_size(width, targeted_height + height_difference)

    def get_highlighted_element(self, generated_code):
        # Extract the assignments from the generated code
        assignment_code = keep_assignments(generated_code)

        # We add imports to the code to be executed
        code = f"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
{assignment_code}
        """.strip()

        local_scope = {"driver": self.driver}

        exec(code, local_scope, local_scope)

        # We extract pairs of variables assigned during execution with their name and pointer
        variable_names = return_assigned_variables(generated_code)

        elements = {}

        for variable_name in variable_names:
            var = local_scope[variable_name]
            if type(var) == WebElement:
                elements[variable_name] = var

        if len(elements) == 0:
            raise ValueError(f"No element found.")

        outputs = []
        for element_name, element in elements.items():
            local_scope = {"driver": self.driver, element_name: element}

            code = f"""
element = {element_name}
driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, "border: 2px solid red;")
driver.execute_script("arguments[0].scrollIntoView({{block: 'center'}});", element)
driver.save_screenshot("screenshot.png")

x1 = element.location['x']
y1 = element.location['y']

x2 = x1 + element.size['width']
y2 = y1 + element.size['height']

viewport_width = driver.execute_script("return window.innerWidth;")
viewport_height = driver.execute_script("return window.innerHeight;")
"""
            exec(code, globals(), local_scope)
            bounding_box = {
                "x1": local_scope["x1"],
                "y1": local_scope["y1"],
                "x2": local_scope["x2"],
                "y2": local_scope["y2"],
            }
            viewport_size = {
                "width": local_scope["viewport_width"],
                "height": local_scope["viewport_height"],
            }
            image = Image.open("screenshot.png")
            output = {
                "image": image,
                "bounding_box": bounding_box,
                "viewport_size": viewport_size,
            }
            outputs.append(output)
        return outputs

    def get_capability(self) -> str:
        return '''

Your goal is to write Selenium code to answer queries.

Your answer must be a Python markdown only.
You can have access to external websites and libraries.
Always target elements by XPATH.

You can assume the following code has been executed:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
```

---

HTML:
<!DOCTYPE html>
<html xpath="/html">
<head xpath="/html/head">
    <title xpath="/html/head/title">Mock Search Page</title>
    <meta charset="utf-8" xpath="/html/head/meta[1]"/>
</head>
<body xpath="/html/body">
    <h1 xpath="/html/body/h1">Search Page Example</h1>
    <input id="searchBar" type="text" placeholder="Type here to search..." xpath="/html/body/input[1]"/>
    <button id="searchButton" xpath="/html/body/button">Search</button>
    <script xpath="/html/body/script">
        document.getElementById('searchButton').onclick = function() {{
            var searchText = document.getElementById('searchBar').value;
            alert("Searching for: " + searchText);
        }};
    </script>
</body>
</html>

Query: Click on the search bar 'Type here to search...', type 'selenium', and press the 'Enter' key

Completion:
```python
# Let's proceed step by step.
# First we need to identify the component first, then we can click on it.

# We use the XPATH to identify the element
search_bar = driver.find_element(By.XPATH, "/html/body/input[1]")

search_bar.click()

# Now we can type the asked input
search_bar.send_keys("selenium")

# Finally we can press the 'Enter' key
search_bar.send_keys(Keys.ENTER)
```

---

HTML:
<!DOCTYPE html>
<html lang="en" xpath="/html">
<head xpath="/html/head">
    <meta charset="UTF-8" xpath="/html/head/meta[1]">
    <title xpath="/html/head/title">Mock Page for Selenium</title>
</head>
<body xpath="/html/body">
    <h1 xpath="/html/body/h1">Welcome to the Mock Page</h1>
    <div id="links" xpath="/html/body/div">
        <a href="#link1" id="link1" xpath="/html/body/div/a[1]">Link 1</a>
        <br xpath="/html/body/div/br[1]">
        <a href="#link2" class="link perf" xpath="/html/body/div/a[2]">Link 2</a>
        <br xpath="/html/body/div/br[2]">
    </div>
</body>
</html>

Query: Click on the title Link 1 and then click on the title Link 2

Completion:
```python
# Let's proceed step by step.
# First we need to identify the first component, then we can click on it. Then we can identify the second component and click on it.

# We use the XPATH to identify the element
link_to_click = driver.find_element(By.XPATH, "/html/body/div/a[1]")

# Then we click on the link
link_to_click.click()

# We use the XPATH to identify the element
link_to_click = driver.find_element(By.XPATH, "/html/body/div/a[2]")

# Click on the element found
link_to_click.click()
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

# To select a paragraph, we can execute a JS script to select the text using the DOM
# In the provided HTML, the third paragraph can be identified using the ID "para3"
# We need to use getElementById to select the paragraph precisely
js_script = """
    // This part depends on the specific HTML, here is the identified ID "para3"
    var para = document.getElementById('para3');
    // The rest is standard
    if (document.body.createTextRange) {{
        var range = document.body.createTextRange();
        range.moveToElementText(para);
        range.select();
    }} else if (window.getSelection) {{
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(para);
        selection.removeAllRanges();
        selection.addRange(range);
    }}
"""

# Then we execute JavaScript
driver.execute_script(js_script)
```

---

HTML:

Query: Scroll up a bit

Completion:
```python
# Let's proceed step by step.
# We don't need to use the HTML data as this is a stateless operation.
# 200 pixels should be sufficient. Let's execute the JavaScript to scroll up.

driver.execute_script("window.scrollBy(0, 200)")
```

---

---

HTML:
<!DOCTYPE html>
<html lang="en" xpath="/html">
<head xpath="/html/head">
    <meta charset="UTF-8" xpath="/html/head/meta[1]">
    <title xpath="/html/head/title">Enhanced Mock Page for Selenium Testing</title>
</head>
<body xpath="/html/body">
    <h1 xpath="/html/body/h1">Enhanced Test Page for Selenium</h1>
    <div class="container" xpath="/html/body/div[1]">
        <button id="firstButton" onclick="alert('First button clicked!');" xpath="/html/body/div[1]/button[1]">First Button</button>
        <!-- This is the button we're targeting with the class name "action-btn" -->
        <button class="action-btn" onclick="alert('Action button clicked!');" xpath="/html/body/div[1]/button[2]">Action Button</button>
        <div class="nested-container" xpath="/html/body/div[1]/div">
            <button id="testButton" onclick="alert('Test Button clicked!');" xpath="/html/body/div[1]/div/button">Test Button</button>
        </div>
        <button class="hidden" onclick="alert('Hidden button clicked!');" xpath="/html/body/div[1]/button[3]">Hidden Button</button>
    </div>
</body>
</html>


Query: Click on the Button 'First Button'

Completion:
```python
# Let's proceed step by step.
# First we need to identify the button first, then we can click on it.

# We use the XPATH to identify the element
action_button = driver.find_element(By.XPATH, "/html/body/div[1]/button[2]")

# Then we can click on it
action_button.click()
```

---
'''
