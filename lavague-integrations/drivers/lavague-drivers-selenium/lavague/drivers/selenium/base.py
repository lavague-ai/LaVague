from typing import Any, Optional, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from lavague.core.base_driver import BaseDriver

class SeleniumDriver(BaseDriver):
    def __init__(self, url: Optional[str] = None, get_selenium_driver: Optional[Callable[[], WebDriver]] = None):
        super().__init__(url, get_selenium_driver)

    def default_init_code(self) -> Any:
        # these imports are necessary as they will be pasted to the output
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        import os.path

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1600,900")

        homedir = os.path.expanduser("~")

        # Paths to the chromedriver files
        path_linux = f"{homedir}/chromedriver-linux64/chromedriver"
        path_testing = f"{homedir}/chromedriver-testing/chromedriver"
        path_mac = (
            "Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        )

        # To avoid breaking change kept legacy linux64 path
        if os.path.exists(path_linux):
            chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
            webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")
        elif os.path.exists(path_testing):
            if os.path.exists(f"{homedir}/chrome-testing/{path_mac}"):
                chrome_options.binary_location = f"{homedir}/chrome-testing/{path_mac}"
            # Can add support here for other chrome binaries with else if statements
            webdriver_service = Service(f"{homedir}/chromedriver-testing/chromedriver")
        else:
            raise FileNotFoundError("Neither chromedriver file exists.")

        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        return driver

    def get_driver(self) -> WebDriver:
        return self.driver

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

    def get_screenshot(self, filename: str) -> None:
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
    
    def get_capability(self) -> str:
        return '''
Your goal is to write Selenium code to answer queries.

Your answer must be a Python markdown only.
You can have access to external websites and libraries.

Don't assume attribute values are unique, use the combination of most available attributes to target precisely the element.
Even if there is mutliple elements doing the same action, choose the most relevant and target it precisely.
Always use //*[contains(@attributes_names ,'value')] to target elements by XPATH.

You can assume the following code has been executed:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Firefox()
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
    <script>
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

# Based on the HTML, the link can be uniquely identified using the ID "searchBar"
# Let's use this ID with Selenium to identify the link
search_bar = driver.find_element(By.XPATH, """//*[contains(@id,"searchBar")][contains(@placeholder,"Type here to search...")]""")

search_bar.click()

# Now we can type the asked input
search_bar.send_keys("selenium")

# Finally we can press the 'Enter' key
search_bar.send_keys(Keys.ENTER)
```

---

HTML:
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mock Page for Selenium</title>
</head>
<body>
    <h1>Welcome to the Mock Page</h1>
    <div id="links">
        <a href="#link1" id="link1">Link 1</a>
        <br>
        <a href="#link2" class="link perf">Link 2</a>
        <br>
    </div>
</body>
</html>

Query: Click on the title Link 1 and then click on the title Link 2

Completion:
```python
# Let's proceed step by step.
# First we need to identify the first component, then we can click on it. Then we can identify the second component and click on it.

# Based on the HTML, the first link the link can be uniquely identified using the ID "link1"
# Let's use this ID with Selenium to identify the link
link_to_click = driver.find_element(By.XPATH, """//*[contains(@id,"link1")][contains(@href,"#link1")]""")

# Then we click on the link
link_to_click.click()

# The other link can be uniquely identified using the class "link" but as it's not unique, we can use the class "perf" to make it more precise
# Let's use this class to identify the link
link_to_click = driver.find_element(By.XPATH, """//*[contains(@class, "link")][contains(@class, "perf")][contains(@href,"#link2")]""")

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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enhanced Mock Page for Selenium Testing</title>
</head>
<body>
    <h1>Enhanced Test Page for Selenium</h1>
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


Query: Click on the Button 'First Button'

Completion:
```python
# Let's proceed step by step.
# First we need to identify the button first, then we can click on it.

# Based on the HTML provided, we need to devise the best strategy to select the button.
# The action button can be identified using the class name "action-btn" as it is unique we don't use contains
action_button = driver.find_element(By.XPATH, """//*[contains(@class,"action-btn")][contains(@onclick,"alert('Action button clicked!");')][contains(.,"Action Button")]""")

# Then we can click on it
action_button.click()
```

---
'''