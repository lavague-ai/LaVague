# Navigate through Notion

LaVague can be used to navigate your Notion spaces and answer questions.

Here is our framework going through a company Notion space to answer the question: **"What's the name of our Lead Developer ?"**


!["notion_demo"](../../assets/notion_demo.gif)

## Try it yourself

We provide a [public notion space](https://maize-paddleboat-93e.notion.site/Welcome-to-ACME-INC-0ac66cd290e3453b93a993e1a3ed272f) with mock data and a few nested documents for you to try LaVague with Notion.

After [installation](../get-started/quick-tour.md), run this code to try LaVague with Notion

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

## Under the hood
To navigate a specific site reliably, we use World Models. World Models are description of typical use cases for navigating a website.

They are hosted on HuggingFace, as you can see when loading the `notion_world_model` on line 8.

To learn more about world models and how they can increase accuracy and reliability, take a look at our dedicated section!

## Tell us about your use cases!

We are always trying to improve LaVague's performance and accuracy and understanding what you want to automate is a core part of making changes. 

- We have a public space for you to add your use cases here! 
- You can also drop a message on our [Discord](https://discord.gg/SDxn9KpqX9) to chat about what you want to do with LaVague!