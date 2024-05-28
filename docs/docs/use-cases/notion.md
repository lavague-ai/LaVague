# Navigate through Notion

LaVague can be used to navigate your Notion spaces and answer questions. 

We have created a [public notion space](https://maize-paddleboat-93e.notion.site/Welcome-to-ACME-INC-0ac66cd290e3453b93a993e1a3ed272f) with mock data and nested documents for you to try this example.

Here is our framework going through several nested pages to answer the question: **"What's the name of our Lead Developer ?"** on this demo space.


!["notion_demo"](../../assets/notion_demo.gif)

On the left, you can see our agent navigating and highlighting the next elements to be interacted with. On the right, the reasoning and the low level instructions generated for our Action Engine (which controls the browser). 

## Try it yourself

After [installation](../get-started/quick-tour.md), create a new .py file and run this code to try LaVague with Notion!

```py
from lavague.core import WebAgent, WorldModel
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine)

agent.get("https://maize-paddleboat-93e.notion.site/Welcome-to-ACME-INC-0ac66cd290e3453b93a993e1a3ed272f")
agent.run("What's the name of our Lead Developer ?")
```

For now we suggest running this code in a Jupyter Notebook while we work on ways to improve the experience when running LaVague locally. 

## Tell us more about your use cases!

Discover community use cases and share yours on our [product feedback space](https://lavague.canny.io/lavague-use-cases). We review your ideas daily to continuously improve LaVague's performance and accuracy on a wide range of tasks.

You can also drop a message on our [Discord](https://discord.gg/SDxn9KpqX9) to chat if you have any questions!