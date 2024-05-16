# Under the Hood

In the [quick tour](./quick-tour.md), we saw an example of how you can quickly build a WebAgent and use it to perform actions for you on the web!

Let's know take a look at how this works.

## Workflow

![LaVague Workflow](../../assets/architecture.png)

1. The user's global objective is handled by the World Model. It considers this objective along with the state of the webpage through screenshots and HTML code, and generate the next step, aka. text instruction, needed to achieve this objective.

2. This instruction is sent to the ActionEngine, which then generates the automation code needed to perform this step and executes it.

3. The World Model then receives new text and image data, aka. a new screenshot and the updated source code, to reflect the updated state of the web page. With this information, it is able to generate the next instruction needed to achieve the objective.

4. This process repeats until the objective is achieved!

## World Model: examples & prompt

When we initialized the World Model in the quick tour, we saw that we must provide a file containing examples showing the World Model the desired thought process and reasoning we wish for it to replicate to generate the next instruction.

In the case of the quick tour, we downloaded an example file from our 'hub' - which is an open-source folder in our GitHub repo, which you can find (and contribute to) [here](https://github.com/lavague-ai/LaVague/tree/main/examples/knowledge)!

You can do this by using the `WorldModel.from_hub()` method and providing the name of the file you wish to download, without the file extension ending, i.e. to download `hf_examples.txt`, you provide `hf_examples` as your argument to this method.
`WorldModel.from_hub()`

!!! World Model initialization options

    Note, as well as pulling an example file from our GitHUb repo with our `from_hub()` method. You can:

    - Specify a path to a local file containing examples by using the `WorldModel.from_local() method`
    - Provide examples directly as a string with the `WorldMethod` default constructor.

Let's take a look at one of the multiple examples including in that file:

```
Objective: Ask the AI model 'Command R plus' 'What is love'
Thought:
- I am on the Hugging Face website.
- Hugging Face is a company that hosts AI models, and allows users to interact with models on them through the chat.
- Therefore, to answer the objective of asking the AI model 'Command R Plus' 'What is love', we need first to find the model page.
- Given the current screenshot, the fastest way to find the model page seems to be to use the search bar.
Instruction: Type 'Command R plus' on the search bar with placeholder "Search ..." and click on the first result
```
These examples are inserted into our full World Model default prompt:

!!! hint "Default World Model prompt in full"

    You are an AI system specialized in high level reasoning. Your goal is to generate instructions for other specialized AIs to perform web actions to reach objectives given by humans.
    Your inputs are an objective in natural language, as well as a screenshot of the current page of the browser.
    Your output are a list of thoughts in bullet points detailling your reasoning, followed by your conclusion on what the next step should be in the form of an instruction.
    You can assume the instruction is used by another AI to generate the action code to select the element to be interacted with and perform the action demanded by the human.

    The instruction should be detailled as possible and only contain the next step. 
    Do not make assumptions about elements you do not see.
    If the objective is already achieved in the screenshot, provide the instruction 'STOP'.

    Here are previous examples:
    ${examples}

    Objective: ${objective}
    Thought:

By providing our `World Model` with examples, we can help our `World Model` to learn to generate instructions by demonstrating the desired thought process and structure for completing tasks.

!!! hint "Contribute knowledge"

    You can contribute knowledge files for a website of your choice, by creating text files with examples of `objectives`, `thoughts` and `instructions` and submitting your file as a `PR` to our GitHub repo.

    See the [contributon section of the docs](../contributing/contributing.md) for more information.