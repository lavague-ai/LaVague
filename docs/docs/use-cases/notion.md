# Navigate through Notion

LaVague can be used to navigate your Notion spaces and answer questions.

Here is our framework going through a company Notion space and several nested pages to answer the question: **"What's the name of our Lead Developer ?"**


!["notion_demo"](../../assets/notion_demo.gif)

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

We are always trying to improve LaVague's performance and accuracy and understanding what you want to automate is a core part of making changes. 

- [Add and discuss your use cases](https://lavague.canny.io/lavague-use-cases) here! We take a look at it every day.
- See a list of [community suggested use cases] that we tried and validated (https://lavague.canny.io/lavague-use-cases?status=complete)!
- You can also drop a message on our [Discord](https://discord.gg/SDxn9KpqX9) to chat if you have any questions!