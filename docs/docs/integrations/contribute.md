
# Custom Contexts

## Creating a custom Context LaVague package

### File structure

To contribute a new LaVague Context, you will need to create a folder for your context within `lavague-integrations/contexts`.

Your folder should be named with the Pypi package name, which should follow this convention: `lavague-contexts-[context_name].

Within this folder, you will need to use the following file structure:

```bash
├── lavague
│   └── contexts
│       └── [context_name]
│           ├── base.py
│           └── __init__.py
├── poetry.lock
├── pyproject.toml
└── README.md
```

#### init.py file

The `init.py` file only requires one line of code:

```py
from lavague.contexts.[context_name].base import [context_name]Context
```

For example:

```py
from lavague.contexts.anthropic.base import AnthropicContext
```

This will import the Context object you define in the `base.py` file.

#### base.py file

This is the key file where you define your context in full.

You will need to import the `lavague.core.context` module, as well as any additional modules needed for your context.

You then define your context as a class that inherits from our base Context module.

This class should initialize the base class with the models of your choice.

Here is a simple example:

```python
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal
from lavague.core.context import Context

class AnthropicContext(Context):
    def __init__(
        self,
        llm: str = "claude-3-5-sonnet-20240620",
        mm_llm: str = "claude-3-5-sonnet-20240620",
        embedding: str = "text-embedding-3-small",
    ) -> Context:
        return super().__init__(
            Anthropic(model=llm),
            AnthropicMultiModal(model=mm_llm),
            OpenAIEmbedding(api_key=openai_api_key),
        )
```

> Note you can add any necessary extra logic, such as checking for API keys before returning your Context.

#### pyproject.toml file

The pyproject.toml file defines the LaVague context package and any necessary dependencies.

You can find out more on how to create a pyproject.toml file [here](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

Feel free to use [one of our other Context's pyproject.toml files](https://github.com/lavague-ai/LaVague/blob/main/lavague-integrations/contexts/lavague-contexts-anthropic/pyproject.toml) as a template and change any necessary values.

#### Lock file

The `poetry.lock` file locks the specific versions of all dependencies of your project. This ensures that anyone who installs the dependencies for your project will get the exact same versions, which helps to maintain consistency across different environments.

You can generate your `lock.file` by running `poetry lock`. However, this step is optional, as we can add the `poetry.lock` file in at a later stage when we publish the package. 

#### README

Your README file will be displayed when we publish the LaVague context package on PyPi on the package's page. 

!!! tip "context package files examples"

    To see examples of all of these files, please refer to the context package folders within our [lavague-integrations/contexts folder](https://github.com/lavague-ai/LaVague/tree/main/lavague-integrations/contexts).

## Contributing your Context

We would be happy to integrate your Contexts for popular models/APIs or high-performing configurations.

To submit your Context for review from our team with the aim of it being integrated into our code base, you should:

- First, clone the LaVague repo.
- Add your Context's package folder into the lavague-integrations/contexts folder
- Test your package locally to ensure it works as expected
- Push your additions to your cloned repo and then create a PR to the official LaVague repo

For more information on how to submit a PR to the repo, see our [contribution guide](https://docs.lavague.ai/en/latest/docs/contributing/general/).
