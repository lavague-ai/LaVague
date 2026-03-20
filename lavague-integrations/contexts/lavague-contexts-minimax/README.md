# MiniMax integration for LaVague

This package provides a [MiniMax](https://www.minimaxi.com/) context for the LaVague web agent framework, enabling the use of MiniMax LLM models (M2.7, M2.5, M2.5-highspeed) and the embo-01 embedding model.

## Installation

```bash
pip install lavague-contexts-minimax
```

## Prerequisites

- A MiniMax API key (set as `MINIMAX_API_KEY` environment variable)
- An OpenAI API key (set as `OPENAI_API_KEY` environment variable, required for multimodal support)

## Usage

```python
from lavague.contexts.minimax import MiniMaxContext

# Uses MINIMAX_API_KEY and OPENAI_API_KEY from environment
context = MiniMaxContext()

# Or specify models explicitly
context = MiniMaxContext(
    llm="MiniMax-M2.5-highspeed",  # 204K context window
    embedding="embo-01",
)
```

See the [examples/agent_minimax.py](../../../examples/agent_minimax.py) for a complete usage example.
