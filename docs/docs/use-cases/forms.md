# Fill out forms

LaVague can be used to fill out simple forms automatically! Just provide the necessary information and ask LaVague to fill event registration forms, job applications, etc. 

We have created a [sample job application form](https://form.jotform.com/241472287797370) you can use to try this use case. 

Here is our framework going through the form and filling it after being given the instruction: **"Fill out this form, my name is: John Doe, my email is john.doe@gmail.com, etc..."**. 


!["notion_demo"](../../assets/jotform_demo.gif)

On the left, you can see our agent navigating and highlighting the next elements to be interacted with. On the right, the reasoning and the low level instructions generated for our Action Engine (which controls the browser). 

## Try it yourself

After [installation](../get-started/quick-tour.md), create a new .py file and run this code to try LaVague with Notion!

```py
from lavague.core import WebAgent, WorldModel, ActionEngine
from lavague.drivers.selenium import SeleniumDriver

selenium_driver = SeleniumDriver()
action_engine = ActionEngine(selenium_driver)
world_model = WorldModel()
agent = WebAgent(world_model, action_engine)

agent.get("https://form.jotform.com/241472287797370")

instruction = """
Fill out this form
Data:
- job: product lead
- name: john doe
- email: john.doe@gmail.com
- phone: 555-123-4567
- cover letter: Excited to work with you!
"""

agent.run(instruction)
```

For now we suggest running this code in a Jupyter Notebook while we work on ways to improve the experience when running LaVague locally. 

## Tell us more about your use cases!

Discover community use cases and share yours on our [product feedback space](https://lavague.canny.io/lavague-use-cases). We review your ideas daily to continuously improve LaVague's performance and accuracy on a wide range of tasks.

You can also drop a message on our [Discord](https://discord.gg/SDxn9KpqX9) to chat if you have any questions!