import yaml
import os


def load_yaml_file(file_path):
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The pricing config file, {file_path} was not found.")
        return None
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return None


def get_pricing_data():
    pricing_file = "pricing_config.yml"
    pricing_file_path = os.path.join(os.path.dirname(__file__), pricing_file)

    data = load_yaml_file(pricing_file_path)
    models = data.get("models", {})
    return models


def build_summary_table(token_summary: dict):
    # calculate totals we don't have from the logs
    total_input = (
        token_summary["world_model_input_tokens"]
        + token_summary["action_engine_input_tokens"]
        + token_summary["total_embedding_tokens"]
    )
    total_output = (
        token_summary["world_model_output_tokens"]
        + token_summary["action_engine_output_tokens"]
    )

    # build table (header)
    header = f"{'Component':<16} | {'Input':<10} | {'Output':<10} | {'Total':<10} | {'Cost (USD)':<10} |\n"
    line = "-" * 70 + "\n"

    # build table (rows)
    world_model_row = f"{'World Model':<16} | {token_summary['world_model_input_tokens']:<10} | {token_summary['world_model_output_tokens']:<10} | {token_summary['total_world_model_tokens']:<10} | $ {token_summary['total_world_model_cost']:<8.4f} |\n"
    action_engine_row = f"{'Action Engine':<16} | {token_summary['action_engine_input_tokens']:<10} | {token_summary['action_engine_output_tokens']:<10} | {token_summary['total_action_engine_tokens']:<10} | $ {token_summary['total_action_engine_cost']:<8.4f} |\n"
    embeddings_row = f"{'Embeddings':<16} | {token_summary['total_embedding_tokens']:<10} | {' ':<10} | {token_summary['total_embedding_tokens']:<10} | $ {token_summary['total_embedding_cost']:<8.4f} |\n"
    total_row = f"{'Total':<16} | {total_input:<10} | {total_output:<10} | {token_summary['total_step_tokens']:<10} | $ {token_summary['total_step_cost']:<8.4f} |\n"

    # combine table
    table = (
        "\n"
        + header
        + line
        + world_model_row
        + action_engine_row
        + embeddings_row
        + line
        + total_row
    )

    return table
