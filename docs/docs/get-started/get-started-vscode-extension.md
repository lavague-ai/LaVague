# Get started: LaVague VSCode Extension **Alpha**

The LaVague VSCode Extension allows you to leverage LaVague directly in VSCode. 

You can generate your automation code and directly preview and test the generated code within VSCode!

!!! warning "Pre-requisites"
    To use our VSCode extension you will need:

    - A version of VSCode >= 1.80
    - The Jupyter notebooks VSCode extension
    - To install a webdriver & LaVague: You can install them with the following command: `wget https://raw.githubusercontent.com/lavague-ai/LaVague/main/setup.sh && sudo bash setup.sh`

    See the LaVague installation instructions [for more details](https://docs.lavague.ai/en/latest/docs/get-started/setting-up-la-vague/)!

### LaVague VSCode Extension in Action

Check out what the LaVague VSCode Extension looks like in action:

<div>
    <img src="https://raw.githubusercontent.com/lavague-ai/lavague/main/docs/assets/vscode-demo.gif" alt="LaVague VSCode Extension Example" style="margin-left: 0px;">
</div>

### Getting started

Firstly, you'll need to download the [LaVague extension from VSCode marketplace](https://marketplace.visualstudio.com/items?itemName=LaVagueAI.lavague).

Now, you can open your first LaVague project:

- Open the VSCode Command Palette with Ctrl+Shift+P

- Type or search and find the 'LaVague: New project' command
<img src="https://github.com/lavague-ai/lavague/blob/main/vscode-assets/command-2.png?raw=true" alt="open new project" width=60%>

- Next you'll be asked to input the URL of the site you wish to perform web actions on.
<img src="https://github.com/lavague-ai/lavague/blob/main/vscode-assets/URL.webp?raw=true" alt="add project URL" width=60%>

This will open a new LaVague project.

### Adding your instruction

We're now ready to add an instruction for the action we'd like to automate following the `%lavague-exec` magic command:

<img src="https://github.com/lavague-ai/lavague/blob/main/vscode-assets/instruction.png?raw=true" alt="add instruction" width=75%>

!!! warning "OpenAI API key"
    You will need to have an OPENAI_API_KEY variable set in your notebook environment. 
    
    If you don't have yours set in your notebook environment, you can add the following code into a cell:

    ```
    import os
    os.environ['OPENAI_API_KEY'] = ''
    ```

If we now run this cell, our automation code will populate the next cell.

<img src="https://github.com/lavague-ai/lavague/blob/main/vscode-assets/instruction-and-code.png?raw=true" alt="generated code" width=75%>

We can then run this generated code to perform the action on our target URL.