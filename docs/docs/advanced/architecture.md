# LaVague Architecture

![architecture](../../assets/architecture.png)

### Command Center ✅

The Command Center is responsible for orchestrating the whole LaVague automation process: taking user input or configurations, pulling information from the Browser, making the relevant calls to the Action Engine, and executing the actions on the Browser.

This could come in various forms, but is currently available as a Python module: `LaVague.CommandCenter`.

### Browser ✅

The browser is controlled by the Command Center to get the state of internet pages and browse. 

### Action Engine ✅

The Action Engine (currently available as a Python module LaVague.ActionEngine) dedicated to handling all the key AI operations behind the scenes. It receives the natural language instructions of the user, such as “Click on the ‘Login’ button”, as well as the HTML source code of the website currently being visited and returns AI-generated executable code to perform this task.

To achieve this, it leverages Retrieval-Augmented Generation by splitting the current HTML code into chunks, finding the ones most likely to answer the query, and using those relevant chunks to generate the code to pilot the browser.

It then uses our default prompt template, which combines the user’s instructions and relevant source code with a carefully constructed prompt template which enables us to attain accurate automation code, currently using Selenium Python code, from the LLM, ready to be executed.

??? info "Default prompts"
    The default prompts was engineered based on principles of Few-shot learning and Chain of Thought. Put simply, we provide the LLM with multiple examples following the same structure: user instructions, HTML source code + the correct Selenium code to automate the task, broken down into clear steps. You can view our default `SELENIUM_PROMPT` at `./src/LaVague/prompts.py`

### Action Store ⌛ (coming soon)

A storage space where actions can optionally be stored. We hope to later integrate this in a community hub of actions.