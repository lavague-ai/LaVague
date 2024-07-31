import logging
import tiktoken
from llama_index.core.callbacks.schema import CBEventType
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core import Settings
from typing import Tuple, List, Any, Optional
from lavague.core.utilities.pricing_util import get_pricing_data
from lavague.core.world_model import WorldModel
from lavague.core.action_engine import ActionEngine
from lavague.core.base_engine import ActionResult
from lavague.core.world_model import WORLD_MODEL_PROMPT_TEMPLATE

# used by gpt-4* models
DEFAULT_TOKENIZER = "o200k_base"


class TokenCounter:
    """
    Token counter for each of MM LLM and embedding models.
    It relies on TokenCountingHandler from llama_index.
    Only one token counter can be used at a time.
    """

    def __init__(
        self,
        log=False,
    ):
        self.pricing_data = get_pricing_data()
        default_tokenizer = tiktoken.get_encoding(DEFAULT_TOKENIZER).encode

        mm_llm_token_counter = TokenCountingHandler(
            tokenizer=default_tokenizer,
            event_starts_to_ignore=[CBEventType.EMBEDDING],
            event_ends_to_ignore=[CBEventType.EMBEDDING],
        )
        embedding_token_counter = TokenCountingHandler(
            tokenizer=default_tokenizer,
            event_starts_to_ignore=[CBEventType.LLM],
            event_ends_to_ignore=[CBEventType.LLM],
        )
        Settings.callback_manager = CallbackManager(
            [mm_llm_token_counter, embedding_token_counter]
        )
        self.mm_llm_token_counter = mm_llm_token_counter
        self.embedding_token_counter = embedding_token_counter

        if log:
            logging_print = logging.getLogger(__name__)
            logging_print.setLevel(logging.INFO)
            format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(format)
            logging_print.addHandler(ch)
            logging_print.propagate = False
            self.logging_print = logging_print
        else:
            self.logging_print = None

    def get_token_count(self, event_type):
        return self.token_counter.get_total_tokens(event_type)

    def process_token_usage(
        self,
        world_model: WorldModel,
        action_engine: ActionEngine,
        result_to_update: Optional[ActionResult] = None,
    ) -> Tuple[dict, dict]:
        """Computes token counts and costs for the current step"""

        if (
            self.embedding_token_counter is not None
            and self.mm_llm_token_counter is not None
        ):
            mm_llm_name = world_model.get_mm_llm_name()
            llm_name = action_engine.get_llm_name()
            embedding_name = action_engine.get_embedding_name()
            # deduplicate and split llm events into world model and action engine events
            deduplicated_events = deduplicate_events(
                self.mm_llm_token_counter.llm_token_counts
            )
            world_model_events, action_engine_events = triage_events(
                deduplicated_events
            )

            # compute llm token counts for each models
            WM_input_tokens, WM_output_tokens, WM_total_tokens = self.count_tokens(
                world_model_events, mm_llm_name
            )
            AE_input_tokens, AE_output_tokens, AE_total_tokens = self.count_tokens(
                action_engine_events, llm_name
            )

            # compute embedding token counts
            embedding_total_tokens = (
                self.embedding_token_counter.total_embedding_token_count
            )

            total_step_tokens = (
                WM_total_tokens + AE_total_tokens + embedding_total_tokens
            )

            token_counts = {
                "world_model_input_tokens": WM_input_tokens,
                "world_model_output_tokens": WM_output_tokens,
                "action_engine_input_tokens": AE_input_tokens,
                "action_engine_output_tokens": AE_output_tokens,
                "total_world_model_tokens": WM_total_tokens,
                "total_action_engine_tokens": AE_total_tokens,
                "total_llm_tokens": WM_total_tokens + AE_total_tokens,
                "total_embedding_tokens": embedding_total_tokens,
                "total_step_tokens": total_step_tokens,
            }

            # compute llm and embedding token costs
            WM_input_cost, WM_output_cost, WM_total_cost = self.calculate_llm_pricing(
                WM_input_tokens, WM_output_tokens, mm_llm_name
            )
            AE_input_cost, AE_output_cost, AE_total_cost = self.calculate_llm_pricing(
                AE_input_tokens,
                AE_output_tokens,
                llm_name,
            )

            total_embedding_cost = self.calculate_embedding_pricing(
                embedding_total_tokens,
                embedding_name,
            )
            total_step_cost = WM_total_cost + AE_total_cost + total_embedding_cost

            token_costs = {
                "world_model_input_cost": WM_input_cost,
                "world_model_output_cost": WM_output_cost,
                "action_engine_input_cost": AE_input_cost,
                "action_engine_output_cost": AE_output_cost,
                "total_world_model_cost": WM_total_cost,
                "total_action_engine_cost": AE_total_cost,
                "total_llm_cost": WM_total_cost + AE_total_cost,
                "total_embedding_cost": total_embedding_cost,
                "total_step_cost": total_step_cost,
            }

            if result_to_update is not None:
                result_to_update.total_estimated_tokens += total_step_tokens
                result_to_update.total_estimated_cost += total_step_cost

            # reset counters
            self.mm_llm_token_counter.reset_counts()
            self.embedding_token_counter.reset_counts()
        else:
            # when token counters are not initialized, we return 0s
            token_counts = {
                "world_model_input_tokens": 0,
                "world_model_output_tokens": 0,
                "action_engine_input_tokens": 0,
                "action_engine_output_tokens": 0,
                "total_world_model_tokens": 0,
                "total_action_engine_tokens": 0,
                "total_llm_tokens": 0,
                "total_embedding_tokens": 0,
                "total_step_tokens": 0,
            }
            token_costs = {
                "world_model_input_cost": 0,
                "world_model_output_cost": 0,
                "action_engine_input_cost": 0,
                "action_engine_output_cost": 0,
                "total_world_model_cost": 0,
                "total_action_engine_cost": 0,
                "total_llm_cost": 0,
                "total_embedding_cost": 0,
                "total_step_cost": 0,
            }

        if self.logging_print:
            counts = [
                f"{key}: {value}" for key, value in token_counts.items() if value > 0
            ]
            if len(counts) > 0:
                self.logging_print.info("Token consumption:\n" + "\n".join(counts))

        return token_counts, token_costs

    def calculate_llm_pricing(
        self, input_token_count: int, output_token_count: int, model: str
    ) -> Tuple[int, int, int]:
        """Computes token costs for LLM according to the pricing data available in pricing_config.yaml"""
        input_pricing = self.pricing_data.get(model, {model: {"input_tokens": 0}}).get(
            "input_tokens", 0
        )
        output_pricing = self.pricing_data.get(
            model, {model: {"output_tokens": 0}}
        ).get("output_tokens", 0)
        token_ratio = self.pricing_data.get(model, {model: {"token_ratio": 1}}).get(
            "token_ratio", 1
        )

        llm_input_token_cost = (input_token_count * input_pricing) / token_ratio
        llm_output_token_cost = (output_token_count * output_pricing) / token_ratio

        llm_cost = llm_input_token_cost + llm_output_token_cost

        return llm_input_token_cost, llm_output_token_cost, llm_cost

    def calculate_embedding_pricing(self, token_count: int, model: str) -> int:
        """Computes token costs for Embedding according to the pricing data available in pricing_config.yaml"""
        embedding_pricing = self.pricing_data.get(
            model, {model: {"input_tokens": 0}}
        ).get("input_tokens", 0)
        token_ratio = self.pricing_data.get(model, {model: {"token_ratio": 1}}).get(
            "token_ratio", 1
        )
        total_embedding_cost = (token_count * embedding_pricing) / token_ratio

        return total_embedding_cost

    def count_tokens(self, events: List[Any], model) -> Tuple[int, int, int]:
        """Helper function to sum token counts for a list of events that belong together"""
        # we use a multiplier to approximate tokens consumed by gemini models based on our default tokenizer

        token_multiplier = self.pricing_data.get(
            model, {model: {"token_multiplier": 1}}
        ).get("token_multiplier", 1)

        input_tokens = (
            sum(event.prompt_token_count for event in events) * token_multiplier
        )
        output_tokens = (
            sum(event.completion_token_count for event in events) * token_multiplier
        )
        total_tokens = (
            sum(event.total_token_count for event in events) * token_multiplier
        )
        return input_tokens, output_tokens, total_tokens


def deduplicate_events(events: List[Any]) -> List[Any]:
    """Helper function to deduplicate events if they are logged twice (temporary fix for #444)"""

    def are_events_equal(event1: Any, event2: Any) -> bool:
        """Helper function to compare two events by their attributes"""
        attributes_to_compare = [
            "prompt",
            "completion",
            "completion_token_count",
            "prompt_token_count",
            "total_token_count",
        ]
        return all(
            getattr(event1, attr) == getattr(event2, attr)
            for attr in attributes_to_compare
        )

    deduplicated = []
    for event in events:
        if not any(
            are_events_equal(existing_event, event) for existing_event in deduplicated
        ):
            deduplicated.append(event)
    return deduplicated


def triage_events(events: List[Any]) -> Tuple[List[Any], List[Any]]:
    """Split events into world model and action engine events based on prompt start"""
    world_model_events = []
    other_events = []

    world_model_prompt_start = WORLD_MODEL_PROMPT_TEMPLATE.template.strip().split("\n")[
        0
    ]

    for event in events:
        if event.prompt.strip().startswith(world_model_prompt_start):
            world_model_events.append(event)
        else:
            other_events.append(event)

    return world_model_events, other_events
