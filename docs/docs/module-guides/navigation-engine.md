# Navigation Engine

The Navigation Engine is the engine dedicated to generating and executing Selenium code to perform an action on a web page.

Let's get to know the Navigation Engine better by removing the usual layers of abstraction and working directly with one directly as an agent would!

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/module-guides/notebooks/NavigationEngine.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open code examples in Colab"></a>

### Initializing a Navigation Engine

First of all, we'll need to create an instance of Navigation Engine.

```python
from lavague.drivers.selenium import SeleniumDriver
from lavague.core.navigation import NavigationEngine


selenium_driver = SeleniumDriver(headless=True, url="https://huggingface.co/docs")
nav_engine = NavigationEngine(selenium_driver)
```

??? note "Optional arguments"

    | **Argument**           | **Type**         | **Description**                                                                                                               | **Default Value**                                                        |
    |------------------------|------------------|-------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
    | `driver`               | `BaseDriver`     | The web driver used to interact with the headless browser. (must be provided)                                                 | None                                                                      |
    | `llm`                  | `BaseLLM`        | This argument can be used to pass an LLM object directly to the NavigationEngine to overwrite the default/context LLM. We support any `llama_index.llms` LLMs. | `None` (defaults to the LLM from the context)                             |
    | `retriever`            | `BaseHtmlRetriever` | The retriever to be used to retrieve the web elements to perform our action on.                                                | `None` (defaults to the retriever based on the driver and embedding)      |
    | `prompt_template`      | `PromptTemplate` | The prompt template used to query the LLM to generate an action.                                                              | `NAVIGATION_ENGINE_PROMPT_TEMPLATE.prompt_template`                       |
    | `extractor`            | `BaseExtractor`  | Specifies how to extract the final code from the LLM's response.                                                              | `DynamicExtractor()`                                                      |
    | `time_between_actions` | `float`          | Time (in seconds) between each action executed by the engine.                                                                 | `1.5` seconds                                                             |
    | `n_attempts`           | `int`            | The number of attempts the LLM should take to generate a valid action. Retries can increase success rate since LLMs are non-deterministic and may succeed even if they fail on the first attempt. | `5` attempts                                                              |
    | `logger`               | `AgentLogger`    | Logger to log the actions taken by the agent.                                                                                 | `None`                                                                    |
    | `display`              | `bool`           | Indicates if the agent is running in `display` mode. This mode can be used when in headless mode to display visual screenshot updates of the agent's progress. | `False`                                                                   |
    | `raise_on_error`       | `bool`           | Whether to raise an exception if an error occurs during execution.                                                            | `False`                                                                   |
    | `embedding`            | `BaseEmbedding`  | This argument can be used to pass an embedding model object directly to the NavigationEngine, which will be used instead of the default/context embedding model. We support any `llama_index.embeddings` models. | `None`                                                                    |

### Retrieval

The first task handled by the Navigation Engine is to perform retrieval on the web page to collect the most relevant chunks, or nodes, of HTML code.

The Navigation Engine's embedding model is used at this stage (here we use the default embedding model, OpenAI's `text-embedding-3-small`).

```python
instruction = "Click on the PEFT section."

nodes = nav_engine.get_nodes(instruction)
```

We can print out these nodes with the following code:

```python
from IPython.display import display, HTML, Code

for node in nodes:
    display(HTML(node)) # Display node as visual element
    display(Code(node, language="html")) # Display code
    print("--------------")
```
![nodes](../../assets/nav-engine-nodes.png)

### Generating automation code

We can now provide these nodes as context for our LLM (here, we use the default LLM, `gpt-4o`) when we generate the appropriate code for our instruction.

```python
context = "\n".join(nodes)

action = nav_engine.get_action_from_context(context, instruction)

display(Code(action, language="python"))
```
![navigation engine code](../../assets/nav-engine-code.png)


### Navigation Engine LLM prompt

The LLM was queried with our default Navigation Engine prompt template which you can view in full [here](https://github.com/lavague-ai/LaVague/blob/9764805bd756d15c83943baa968d35f979242314/lavague-core/lavague/core/navigation.py#L28).

![navigation engine prompt](../../assets/nav-engine-prompt-template.png)

We see that the prompt is made up of three parts:

- The `driver capability` or driver prompt template
- The `context string`, or retrieved nodes
- The `query` itself - this will be the original instruction received by the Navigation Engine from the World Model

We can see the default Selenium driver prompt template with the following code (or view the full code [here](https://github.com/lavague-ai/LaVague/blob/9764805bd756d15c83943baa968d35f979242314/lavague-integrations/drivers/lavague-drivers-selenium/lavague/drivers/selenium/base.py#L177)):

```python
print(nav_engine.prompt_template)
```
![Selenium prompt template](../../assets/selenium-driver-prompt-template.png)

