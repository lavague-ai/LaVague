import re


def quote_numeric_yaml_values(yaml_string: str) -> str:
    """Wrap numeric values in quotes in a YAML string.

    This is helpful when the YAML might contain numeric values that are not wrapped in quotes which can cause issues when parsing the YAML.
    In Navigation Engine, we expect values to be always strings, so this avoids issues when the YAML does not wrap numeric values in quotes, such as outputting "value: 01" instead of "value: '01'".
    """

    def replace_value(match):
        full_match, value = match.groups()
        try:
            # Try to convert to float to catch both integers and decimal numbers
            float(value)
            # If successful, it's a number, so wrap it in quotes
            return f'value: "{value}"'
        except ValueError:
            # If it's not a number, return the original match
            return full_match

    # Regex to match 'value:' followed by a space and then any numeric
    pattern = r"(value: ([\d.]+))"

    # Replace values that are numeric
    modified_yaml = re.sub(pattern, replace_value, yaml_string)

    return modified_yaml
