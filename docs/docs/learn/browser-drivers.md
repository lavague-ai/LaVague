
# Browser Drivers

Drivers are interfaces for interacting with web browsers autonomously.

Our Driver module provides an interface for interacting with web browsers, offering additional utility functions for easier browser automation and interaction.

## SeleniumDriver

Currently, our Driver module supports Selenium Web Drivers. By default, it starts a headless session with a blank user session.

| Parameter        | Type    | Default | Description                                                                                                         |
|------------------|---------|---------|---------------------------------------------------------------------------------------------------------------------|
| **headless**     | `bool`  | `False` | Determines whether to hide or show the browser UI. Set to `True` to run the browser in headless mode.               |
| **user_data_dir**| `str`   | `None`  | Path to your Chrome profile directory. If left empty, Chrome starts a fresh session every time. If provided, Chrome starts with your profile's settings and data, this can help avoid bot protections  |

### Example

Below is an example of how to initialize `SeleniumDriver` to display the browser interface and start the session from your profile.

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="path/to/your/chrome/profile")
```

### Finding Your Chrome Profile Path

To use your existing Chrome profile, you'll need to locate the profile path on your operating system. Here are the default locations for Windows, Linux, and OSX:

- **Windows**: `C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data`
- **Linux**: `/home/<YourUsername>/.config/google-chrome`
- **OSX**: `/Users/<YourUsername>/Library/Application Support/Google/Chrome`

Replace `<YourUsername>` with your actual username to navigate to the correct path.

Using the appropriate path from your system, you can easily start Chrome with your user profile:

```python
from lavague.drivers.selenium import SeleniumDriver
driver = SeleniumDriver(headless=False, user_data_dir="C:/Users/YourUsername/AppData/Local/Google/Chrome/User Data")
```

With this setup, you can leverage your existing Chrome data and settings for a seamless automated browsing experience.
