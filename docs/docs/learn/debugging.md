# End-to-end debugging

When using LaVague, you may find that our Web Agents are not always able to successfully achieve the objective you set them out of the box, leading to either incorrect results or `Navigation errors`.

Our Agents are designed to be as customizable as possible so you can adjust components to get the best result for your particular use case.

!!! hint "Common issues"

    Problems with performance usually stem from one of three components: 

    - The World Model
    - The Retriever
    - The Action Engine

In this guide, we'll take a look at how you can debug and make adjustments to rectify issues with each of these components.

## The World Model

!!! abstract "Case one"
    The World Model's is either providing the Action Engine with poor instructions.

### How to detect World Model performance issues?

Bad instructions from the World Model should be simple to spot and debug since the World Model outputs its "thoughts" and next instruction in real-time. WE can verify the outputted instructions seem appropriate for achieving our objective.

### How to improve World Model performance?

#### Adding knowledge to World Model prompt

In the following example, we set an objective to "Return the temperature now in Birmingham UK?"" on "weather.com":

```python
selenium_driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(driver=selenium_driver)
agent = WebAgent(world_model, action_engine)

url = "https://weather.com/"
objective = "What is the temperature now in Birmingham UK?"
agent.get(url)
ret = agent.run(objective)
print(ret.output)
```

As a user, we quickly notice that when we search for a location on the website, the search button does not appear to be functioning and is unresponsive; instead a drop-down list with clickable links loads for the locations based on my search entry.

In our first attempt at using LaVague to achieve our objective, the World Model does not understand that the search button is not working on this website and keeps instructing the Action Engine to click on the search button, causing `navigation errors`:

![navigation-error](../../assets/weather-navigation-errors.png)

We can teach our World Model to behave differently and produce different instructions by providing it with extra knowledge.

For this example, we can provide the World Model with the following knowledge saved in a `knowledge.txt file`:

!!! note "Knowledge.txt file"
    We should not press the search button. Instead we should just type a search entry into the search bar and then wait for 3 seconds must be sure to wait for 3 seconds.

    Example:

    Thoughts:
    - The screenshot shows the homepage of the website 'weather.com'.
    - The objective is to return the current temperature in the location you wish to search for
    - The best next step is to use the Navigation Engine to search for the location on the website.
    Next engine: Navigation Engine
    Instruction:
    - Click on the search bar.
    - Type the location in the search bar.
    - Enforce a pause of 3 seconds

We send this extra knowledge to the World Model by providing the path to our `knowledge.txt` file to the `WorldModel.add_knowledge()` method:

```python
world_model = WorldModel()
world_model.add_knowledge(file_path="knowledge.txt")
```

If I retry running the agent with this updated World Model with my original objective, the World Model now gives the following first set of instructions:

![corrected-instructions](../../assets/weather-corrected-instructions.png)

By not clicking on the search button after typing in the search bar, and instead pausing, we avoid a series of errors and the website has time to load its drop-down menu, which will then be taken into consideration in the screenshot taken by the World Model when creating its next set of instructions.

![drop-down-weather](../../assets/weather-dropdown.png)

The World Model is then able to click on the link to the Birmingham weather page and correctly return the current temperature in Birmingham, UK.

![Birmingham weather page](../../assets/weather-birmingham-page.png)
![correct results](../../assets/weather-success.png)

✅ By adding a small amount of text knowledge, we were able to teach our World Model how to navigate correctly on this website.

## The Retriever

!!! abstract "Case two"
    The World Model has sent the Action Engine a correct instruction, but the Navigation Engine fails to generate code targetting the correct HTML element because the retriever did not retrieve the relevant HTML element and pass it onto the LLM, so the LLM could not find and target the correct element with its code.

> Note the retriever is only used when the next instruction is sent to the `Navigation Engine`

### How to detect Retriever performance issues?

It is, again, relatively straight-forward to know if an action is failing due to the Retriever.

The Retriever is part of the Action Engine workflow and selects the top X (5 by default) HTML elements that it identifies as most relevant to complete the current instruction. 

We can display these retrieved HTML elements, or nodes, and visually verify that they do indeed include the relevant HTML element needed to complete the instruction.

For example, if the instruction is to 'Type LaVague in the search bar', we could expect the retrieved nodes to include the search bar.

To view the nodes for each step (instruction sent to the Action Engine by the World Model). You can use the `display_previous_nodes` method:

```python
step = 0 # View nodes retrieved for first instruction
agent.display_previous_nodes(step)
```

This will provide both a visual representation and the HTML code for each element retrieved.

![nodes](../../assets/nodes.png)

### How to improve Retriever performance?

There are a few ways in which we can adjust the retriever for improved performance.

#### Modifying the retriever

##### rank_fields

The `rank_fields` option defines the attributes of HTML elements that will be considered for ranking relevance when retrieving the most relevant elements. By default we take into account the`element`, `placeholder`, `text` and `name` attributes.

To take an example, we can imagine our Action Engine receives the instruction `Type Sarah into the first name form field` but fails to retrieve the relevant `first name` text input field.

We can inspect the HTML of this element by right-clicking and selecting `inspect` on this webpage in our browser.

```html
<input type="text" id="fname" value="John">
```

If the HTML code is as seen above, we might decide to add the `type` and `id` fields to our `rank_fields` argument.

```python
retriever = OpsmSplitRetriever(rank_fields=["element", "placeholder", "text", "name", "type", "id"])
action_engine = ActionEngine(driver=SeleniumDriver(), retriever=retriever)
agent = WebAgent(WorldModel(), action_engine)
```

##### top_k

By default, the retriever will pass on the 5 most relevant nodes it finds to the LLM, which uses this information to generate code targetting the XPATH of the correct element.

We can try to increase the likelihood of the retriever finding the correct node by to increasing the X most relevant number of nodes the Retriever will return:

```python
retriever = OpsmSplitRetriever(top_k=10)
action_engine = ActionEngine(driver=SeleniumDriver(), retriever=retriever)
agent = WebAgent(WorldModel(), action_engine)
```

#### Changing retrievers

We can also test out performance with different retrievers for your task.

In the following example, we select the retriever to the built-in `CohereRetriever` from the optional package `lavague-retrievers-cohere`.

```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium import SeleniumDriver
from lavague.retrievers.cohere import CohereRetriever

retriever = CohereRetriever()
action_engine = ActionEngine(driver=SeleniumDriver(), retriever=retriever)
agent = WebAgent(WorldModel(), action_engine)
```

!!! note "Evaluating Retrievers"

    See our [Evaluator module guide](https://docs.lavague.ai/en/latest/docs/learn/evaluation/) for details on how to evaluate Retriever performance.

### The Action Engine's LLM

!!! abstract "Case three"
    The Navigation or Python Engine has received a correct instruction and (in the case of the Navigation Engine) has the correct nodes, but it is still generating incorrect code.

### Adding knowledge or examples to LLM prompt

!!! note "🚧🔨⏳ Coming soon"

    We are currently changing our framework to make it easier to modify the Selenium or Playwright prompt leveraged by the Navigation Engine to produce code. Instructions will be added here after this update.

    See our [GitHub issue](https://github.com/lavague-ai/LaVague/issues/361) to follow out progress.

### Changing the LLM

We can also change the LLM we use to complete our task.

In the following example, we set our Action Engine to use Gemini's `1.5-flash-latest` LLM:

```python
from llama_index.llms.gemini import Gemini
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
# Customizing the LLM, multi-modal LLM and embedding models
llm = Gemini(model_name="models/gemini-1.5-flash-latest")

action_engine = ActionEngine(driver=driver, llm=llm, embedding=embedding)
agent = WebAgent(WorldModel(), action_engine)

```

!!! note "Evaluating LLMs"

    See our [Evaluator module guide](https://docs.lavague.ai/en/latest/docs/learn/evaluation/) for details on how to evaluate LLM performance.