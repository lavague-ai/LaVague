# Navigate through Notion

LaVague can be used to navigate your Notion spaces and answer questions.

Here is our framework going through a company Notion space and several nested pages to answer the question: **"What's the name of our Lead Developer ?"**


!["notion_demo"](../../assets/notion_demo.gif)

On the left you can see the Browser being automated and the next interaction highlighted in red. On the right is the world model thoughts and instructions given to our Action Engine.


## Try it yourself

We provide a [public notion space](https://maize-paddleboat-93e.notion.site/Welcome-to-ACME-INC-0ac66cd290e3453b93a993e1a3ed272f) with mock data and a few nested documents for you to try this example.

After [installation](../get-started/quick-tour.md), create a new .py file and run this code to try LaVague with Notion

```py
from lavague.defaults import default_get_selenium_driver
from lavague.action_engine import ActionEngine
from lavague.world_model import GPTWorldModel
from lavague.agents import WebAgent

driver = default_get_selenium_driver()
action_engine = ActionEngine()
world_model = GPTWorldModel.from_hub("notion_world_model")

agent = WebAgent(driver, action_engine, world_model)

agent.get("https://maize-paddleboat-93e.notion.site/Welcome-to-ACME-INC-0ac66cd290e3453b93a993e1a3ed272f")
agent.run("What's the name of our Lead Developer ?")
```

For now we suggest running this code in a Jupyter Notebook while we work on ways to improve the experience when running LaVague locally. 

## Tell us more about your use cases!

Discover community use cases and share yours on our [product feedback space](https://lavague.canny.io/lavague-use-cases). We review your ideas daily to continuously improve LaVague's performance and accuracy on a wide range of tasks.

You can also drop a message on our [Discord](https://discord.gg/SDxn9KpqX9) to chat if you have any questions!