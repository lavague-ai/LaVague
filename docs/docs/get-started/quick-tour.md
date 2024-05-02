# LaVague Quick Tour

In this quick tour, we'll show you how to use the LaVague CLI to perform actions on web from natural language instructions.

If you prefer to run this quick tour as end-to-end Google Colab notebook, follow [this link](https://colab.research.google.com/github/lavague-ai/lavague/blob/main/docs/docs/get-started/quick-tour-notebook/quick-tour.ipynb)

!!! note "Pre-requisites"
    - Make sure you've already [installed LaVague](https://docs.lavague.ai/en/latest/docs/get-started/setting-up-la-vague/)
    - Our default demo uses the OpenAI API. You will need to have an OPENAI_API_KEY environment variable set in your local environment

    To use LaVague with different APIs, see our [integrations section](https://docs.lavague.ai/en/latest/docs/integrations/home/)

## LaVague Launch
<div>
    <img src="https://raw.githubusercontent.com/lavague-ai/lavague/main/docs/assets/lavague_launch_hn.gif" alt="LaVague Launch Example">
</div>
You can launch an interactive in-browser Gradio demo where you can test out instructing LaVague to perform actions on a website with the following command:

```bash
lavague launch
```

??? info "Optional arguments"
    You can specify a custom URL and instructions or LaVague configuration with the following arguments:

    - The `--instructions` or `-i` option accepts a yaml file containing: the URL of the website we will interact with & the instructions for the actions we wish to automate
    -  The `--config` or `-c` option with a Python file which can be used to set a desired LLM, embedder etc.

    For more information, see the [customization guide](https://docs.lavague.ai/en/latest/docs/get-started/customization/)!

You can now click on the public (if you are using Google Colab) or local URL to open your interactive LaVague demo.

!!! note "How to use Gradio demo"

    1. Click on the URL textbox and press enter. This will show a screenshot of your initial page.

    2. Select an instruction or write your own, and again click within the instruction textbox and press enter.

    Feel free to test out different URLs and instructions.



## LaVague Build
<div>
    <img src="https://raw.githubusercontent.com/lavague-ai/lavague/main/docs/assets/lavague_build_hn.gif" alt="LaVague Build Example">
</div>

Alternatively, you can use the `build` command to generate the automation code directly without launching a Gradio demo:

```bash
lavague build
```

This will create an automation script in your current directory named `output_gen.py`.

You can then inspect the code and execute it locally!

### Support

If you have any further questions, join us on the LaVague Discord [here](https://discord.com/invite/SDxn9KpqX9).