# Driver

### Overview
The Driver module provides an interface for interacting with web browsers. This module offers additional utility functions for easier browser automation and interaction.

## SeleniumDriver

At the moment, our Driver only supports Selenium Web Drivers. By default, it starts a headless session with a clean profile.

### Parameters

- **headless** (`bool` optional): hide/show the browser UI. `False` by default.
- **user_data_dir** (`str` optional): start Chrome from an existing profile. 

Provide the path to your chrome sessions to start Chrome with your profile. Leave it empty to start a fresh Chrome session everytime. This helps not having to log in to your sites everytime, or mitigate bot protection.

### Example

Here's an example of how to initialize `SeleniumDriver` to display the browser interface and start the session from your profile. 

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, chrome_user_dir="path/to/your/chrome/profile")
```
