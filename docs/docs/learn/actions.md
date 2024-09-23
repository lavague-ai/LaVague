# Action objects

Trajectories objects will always contain a list of `Action objects`, which provide information about each action generated and executed by an agent, as well as all the information needed to replay these actions.

![action chain](https://raw.githubusercontent.com/lavague-ai/LaVague/drafting-some-docs/docs/assets/actions.png)

## Navigation actions

In the case of web navigation, an agent will generate an action based on a pre-defined list of possible actions. The action is provided as a string following a JSON format with all the key-pair arguments needed to easily parse and perform navigation actions. 

```json
action:
        args:
            xpath: "/html/body/section/devsite-header/div/div[1]/div/div/div[2]/div[1]/devsite-tabs/nav/tab[2]/a"
        name: "click"
```

Here is a list of the current possible actions an agent can perform and the arguments required for this action:

| Name              | Arguments                                  | Description                                                                                                      | Engine             |
|-------------------|--------------------------------------------|------------------------------------------------------------------------------------------------------------------|--------------------|
| click             | xpath                            | Click on an element with a specific xpath.                                                                       | NavigationEngine   |
| setValue          | xpath, value              | Focus on and set the value of an input element with a specific xpath.                                             | NavigationEngine   |
| dropdownSelect    | xpath, value               | Select an option from a dropdown menu by its value.                                                              | NavigationEngine   |
| setValueAndEnter  | xpath, value               | Sets a value and presses ENTER. Used to submit forms without a submit button.                                    | NavigationEngine   |
| hover             | xpath                              | Moves the mouse cursor over an element identified by the xpath, useful for revealing dropdown menus.  | NavigationEngine   |
| scroll            | xpath, value (UP/DOWN)     | Scrolls the container holding the element identified by the xpath, either up or down.                            | NavigationEngine   |
| SCROLL_DOWN       |                                       | Scrolls the browser window down.                                                                                 | NavigationControl  |
| SCROLL_UP         |                                        | Scrolls the browser window up.                                                                                   | NavigationControl  |
| WAIT              |                                        | Pauses the operation for a set duration (e.g., 5 seconds).                                                       | NavigationControl  |
| BACK              |                                        | Navigates back to the previous page.                                                                             | NavigationControl  |
| MAXIMIZE_WINDOW   |                                        | Maximizes the browser window.                                                                                    | NavigationControl  |
| SWITCH_TAB        | tab_id                            | Switches to a specific browser tab based on the tab_id provided.                                                 | NavigationControl  |