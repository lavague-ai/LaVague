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
    print(data)
    models = data.get("models", {})
    print(models)
    return models
