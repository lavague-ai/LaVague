# Understanding token usage and cost

LaVague uses LLMs to reason and interact with web pages. LLM inference consumes tokens and estimating pricing for different use cases is possible with the LaVague `TokenCounter` module.

This allow an in-depth understanding of all the factors influencing the cost at each step of an agent's task. **Pricing estimation currently only supports `gpt-4o` and `text-embedding-3-large`**.

!!! warning "`TokenCounter` is currently not enabled by default"

    While we keep testing and improving this feature, you'll need to manually enable the `TokenCounter` to track your usage. Keep on reading this documentation to learn how. 


## Available metrics

Token counts are separated in three main categories

- WorldModel: **multi-modal llm tokens**
- ActionEngine: **llm tokens**
- PythonEngine (if used): **embeddings**

We also differentiate **input** and **output** tokens in the case of llm consumption since pricing is usually different for each of these token types. 

This allows for an in-depth tracking of all the different agent components that are consuming tokens from external providers. 

| **Variable Name**                  | **Explanation**                                                            | **Example Value** |
|------------------------------------|----------------------------------------------------------------------------|-------------------|
| **world_model_input_tokens**       | The number of tokens given as input to the world model.                     | 3145              |
| **world_model_output_tokens**      | The number of tokens produced as output by the world model.                 | 79                |
| **action_engine_input_tokens**     | The number of tokens given as input to the action engine.                   | 6279              |
| **action_engine_output_tokens**    | The number of tokens produced as output by the action engine.               | 88                |
| **total_world_model_tokens**       | The total number of tokens processed by the world model (input + output).   | 3224              |
| **total_action_engine_tokens**     | The total number of tokens processed by the action engine (input + output). | 6367              |
| **total_llm_tokens**               | The total number of tokens processed by the entire model (world + action).  | 9591              |
| **total_embedding_tokens**         | The total number of tokens used for embeddings, if any (0 in this case).    | 0                 |
| **total_step_tokens**              | The total number of tokens processed in one complete step of the model.     | 9591              |
| **world_model_input_cost**         | The cost associated with the input tokens of the world model.               | $0.015725         |
| **world_model_output_cost**        | The cost associated with the output tokens of the world model.              | $0.001185         |
| **action_engine_input_cost**       | The cost associated with the input tokens of the action engine.             | $0.031395         |
| **action_engine_output_cost**      | The cost associated with the output tokens of the action engine.            | $0.00132          |
| **total_world_model_cost**         | The total cost for the world model (input + output costs).                  | $0.016909         |
| **total_action_engine_cost**       | The total cost for the action engine (input + output costs).                | $0.032715         |
| **total_llm_cost**                 | The total cost for the entire model (world model + action engine costs).    | $0.049625         |
| **total_embedding_cost**           | The cost associated with embeddings, if any (0 in this case).               | $0.0              |
| **total_step_cost**                | The total cost for one complete step of the model.                          | $0.049625         |


## Enable token logging

To enable logging of all tokens consumed: 
- import the `TokenCounter` module
- create a `TokenCounter` object before any other modules to register all callbacks properly
- include it as a parameter when creating the `WebAgent`

!!! warning "Initialize `TokenCounter` before all other modules"

    We use callbacks to count tokens, make sure to declare the counter as the very first module to make sure all callbacks will be properly registered and ensure all tokens will be counter. 


```python
from lavague.core import WorldModel, ActionEngine
from lavague.core.agents import WebAgent
from lavague.drivers.selenium.base import SeleniumDriver

# import TokenCounter
from lavague.core.token_counter import TokenCounter

# instantiate it before all other modules
token_counter = TokenCounter(log=True)

driver = SeleniumDriver(headless=False)
world_model = WorldModel()
action_engine = ActionEngine(driver)

# pass the TokenCounter to the agent
agent = WebAgent(
    world_model,
    action_engine,
    token_counter=token_counter,
    
)

# run the agent
agent.get("https://huggingface.co/docs")
agent.run("Go on the quicktour of PEFT", log_to_db=True)

# get logs
log_df = agent.logger.return_pandas()

# compute and show steps taken, tokens consummed and cost
total_cost = log_df["total_step_cost"].sum()
total_tokens = log_df["total_step_tokens"].sum()
total_steps = len(log_df)

print("Total steps:", total_steps)
print(f"Total tokens: {total_tokens}")
print(f"Total cost: ${round(total_cost, 3)}")

```

Tokens consumed will be logged along cost estimations. To learn more about different ways of accessing those logs, please visit our [Logger documentation](../learn/local-log.md). 


## Current support

### Counting tokens
This module can only track token usage from `llama-index` supported models. To learn how to use other models, please visit our [customization guide](./customization.md).

### Price estimations
Prices are defined and calculated according to our `pricing_config.yaml` file. You can find the [most up to date version of this file](https://github.com/lavague-ai/LaVague/blob/main/lavague-core/lavague/core/utilities/pricing_config.yml) in our repository.

Currently we support price estimations for the following models: 

- llms: 
    - `gpt-4o`
- embeddings:
    - text-embedding-3-large
