


| Name              | Arguments                                  | Description                                                                                                      | Engine             |
|-------------------|--------------------------------------------|------------------------------------------------------------------------------------------------------------------|--------------------|
| click             | xpath: string                              | Click on an element with a specific xpath.                                                                       | NavigationEngine   |
| setValue          | xpath: string, value: string               | Focus on and set the value of an input element with a specific xpath.                                             | NavigationEngine   |
| dropdownSelect    | xpath: string, value: string               | Select an option from a dropdown menu by its value.                                                              | NavigationEngine   |
| setValueAndEnter  | xpath: string, value: string               | Sets a value and presses ENTER. Used to submit forms without a submit button.                                    | NavigationEngine   |
| hover             | xpath: string                              | Moves the mouse cursor over an element identified by the xpath, useful for revealing tooltips or dropdown menus.  | NavigationEngine   |
| scroll            | xpath: string, value: string (UP/DOWN)     | Scrolls the container holding the element identified by the xpath, either up or down.                            | NavigationEngine   |
| SCROLL_DOWN       | none                                       | Scrolls the browser window down.                                                                                 | NavigationControl  |
| SCROLL_UP         | none                                       | Scrolls the browser window up.                                                                                   | NavigationControl  |
| WAIT              | none                                       | Pauses the operation for a set duration (e.g., 5 seconds).                                                       | NavigationControl  |
| BACK              | none                                       | Navigates back to the previous page.                                                                             | NavigationControl  |
| SCAN              | none                                       | Placeholder action, does nothing (pass).                                                                         | NavigationControl  |
| MAXIMIZE_WINDOW   | none                                       | Maximizes the browser window.                                                                                    | NavigationControl  |
| SWITCH_TAB        | tab_id: number                             | Switches to a specific browser tab based on the tab_id provided.                                                 | NavigationControl  |


