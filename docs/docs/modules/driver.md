# Driver

### Overview
The Driver module provides an interface for interacting with web browsers. This module offers additional utility functions for easier browser automation and interaction.

## SeleniumDriver

At the moment, our Driver only supports Selenium Web Drivers. By default, it starts a headless session with a clean profile.

### Parameters

- **headless** (`bool` optional): hide/show the browser UI. `False` by default.
- **user_data_dir** (`str` optional): start Chrome from an existing profile. 

Provide the path to your chrome sessions to start Chrome with your profile. Leave it empty to start a fresh Chrome session. This helps not having to log in to your sites each time you start a new agent, or mitigate bot protection.

- **debug_address** (`str` optional): bind to an already running Chrome instance (has to be in debug mode)

You may want to launch LaVague on already existing Chrome instances, to do that, start Chrome in debug mode, then provide the `ip:port` of your instance in this parameter. Note that `headless` and `user_data_dir` are optional in this case since launching Chrome in debug mode will always start from your default user profile. 


## Examples

Start by importing SeleniumDriver
```python
from lavague.drivers.selenium import SeleniumDriver
```

### Start a headless fresh session

By default, we run the browser in headless and without any profile. 

```python
driver = SeleniumDriver()
```


### Start a new session with your profile and display the UI
Here's an example of how to initialize `SeleniumDriver` to display the browser interface and start the session from your profile. 

```python
driver = SeleniumDriver(headless=False, chrome_user_dir="path/to/your/chrome/profile")
```

### Bind to an already exising instance running in debug mode

Here's how to bind to an already existing Chrome instance running in debug mode. 

First, make sure to **start Chrome in debug mode** and provide a port.

OSX Terminal
```bash
open -na "Google Chrome" --args --remote-debugging-port=9222
```

Windows Command Prompt: 
```bash
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

Linux Terminal: 
```bash
google-chrome --remote-debugging-port=9222
```

Then, initialize the Driver with the `debug_address` parameter and make sure you're passing the same port as Step 1. 
```python
driver = SeleniumDriver(debug_address="localhost:9222")
```
