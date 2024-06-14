# LaVague Gradio Agent Demo

### What is LaVague's Gradio Agent Demo?

Our agents have a `demo` method, which will launch an interactive demo which we can access by clicking on the public or local URL generated. 

We can use this `demo mode` to can interact with LaVague in our browser, testing out various different objectives on different URLs and viewing the Agent's progress and output in a chat user interface.

You can take a quick look at this feature in the video below:

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="https://github.com/lavague-ai/LaVague/blob/main/docs/assets/gradio.webm?raw=true" type="video/webm">
  </video>
</figure>

### How to launch a LaVague Agent demo

<a target="_blank" href="https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/notebooks/Gradio.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open code example in Colab"></a>

To launch a LaVague Agent demo, we set up our Agent as in the usual way, as seen in the [quick tour guide](https://docs.lavague.ai/en/latest/docs/get-started/quick-tour/). Once we have our Agent, we can run the `agent.demo()` method to launch our Gradio Agent Demo.

```python
# We should set no_load_strategy to True when using the demo() method
driver = SeleniumDriver(headless=True, no_load_strategy=True)
action_engine = ActionEngine(driver)
world_model = WorldModel()

agent = WebAgent(world_model, action_engine)

# Set our URL
agent.get("https://huggingface.co/docs")

# Launch our demo with our objective
agent.demo("Go on the quicktour of PEFT")
```

!!! note "Gradio Agent Demo no_load_strategy"
    For faster performance when using the `agent.demo()` method, you should set the `no_load_strategy` Driver option to True.

    This turns off Selenium's default load strategy that waits for the page to be fully loaded before giving you back control which was causing a significant slowdown with our `Gradio Agent Demo`. Instead, LaVague will detect when the page is loaded.

    This option is not recommended with the `agent.run()` method however.

### Optional arguments

The `agent.run()` has the two following optional arguments:

- objective: A string objective that will pre-populate the objective on the Gradio demo
- user_data: Any input data you want to pass to the agent, such as the data to be used for filling in an application form