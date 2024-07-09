import tiktoken
from llama_index.core.callbacks.schema import CBEventType
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core import Settings


def init_token_counter(
    mm_llm_name="gpt-4o", embedding_model_name="text-embedding-3-large"
):
    """
    Initializing two token counters for each of MM LLM and embedding models
    """
    mm_llm_token_counter = TokenCountingHandler(
        tokenizer=tiktoken.encoding_for_model(mm_llm_name).encode,
        event_starts_to_ignore=[CBEventType.EMBEDDING],
        event_ends_to_ignore=[CBEventType.EMBEDDING],
    )
    embedding_token_counter = TokenCountingHandler(
        tokenizer=tiktoken.encoding_for_model(embedding_model_name).encode,
        event_starts_to_ignore=[CBEventType.LLM],
        event_ends_to_ignore=[CBEventType.LLM],
    )
    Settings.callback_manager = CallbackManager(
        [mm_llm_token_counter, embedding_token_counter]
    )
    return {
        "llm_token_counter": mm_llm_token_counter,
        "embedding_token_counter": embedding_token_counter,
    }
