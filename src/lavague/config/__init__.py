import os
import os.path as osp
import shutil

import yaml

here = osp.dirname(osp.abspath(__file__))

def update_dict(target_dict, new_dict, validate_item=None):
    for key, value in new_dict.items():
        if validate_item:
            validate_item(key, value)
        if key not in target_dict:
            continue
        if isinstance(target_dict[key], dict) and isinstance(value, dict):
            update_dict(target_dict[key], value, validate_item=validate_item)
        else:
            target_dict[key] = value


# -----------------------------------------------------------------------------


def get_default_config():
    config_file = osp.join(here, "default_config.yaml")
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # save default config to ~/.labelmerc
    user_config_file = osp.join(osp.expanduser("~"), ".labelmerc")
    if not osp.exists(user_config_file):
        try:
            shutil.copy(config_file, user_config_file)
        except Exception:
            pass

    return config


def validate_config_item(key, value):
    if key == "validate_label" and value not in [None, "exact"]:
        raise ValueError(
            "Unexpected value for config key 'validate_label': {}".format(
                value
            )
        )
    if key == "shape_color" and value not in [None, "auto", "manual"]:
        raise ValueError(
            "Unexpected value for config key 'shape_color': {}".format(value)
        )
    if key == "labels" and value is not None and len(value) != len(set(value)):
        raise ValueError(
            "Duplicates are detected for config key 'labels': {}".format(value)
        )


def get_config(config_file_or_yaml=None, config_from_args=None):
    config_file = osp.join(here, "default_config.yaml")
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # 환경 변수 처리
    config = update_config_with_env_vars(config)

    # save default config to ~/.labelmerc
    user_config_file = osp.join(osp.expanduser("~"), ".labelmerc")
    if not osp.exists(user_config_file):
        try:
            shutil.copy(config_file, user_config_file)
        except Exception:
            pass

    if config_file_or_yaml is not None:
        config_from_yaml = yaml.safe_load(config_file_or_yaml)
        if not isinstance(config_from_yaml, dict):
            with open(config_from_yaml) as f:
                config_from_yaml = yaml.safe_load(f)
        update_dict(
            config, config_from_yaml, validate_item=validate_config_item
        )

    if config_from_args is not None:
        update_dict(
            config, config_from_args, validate_item=validate_config_item
        )

    return config


def update_config_with_env_vars(config):
    for key, value in config.items():
        if isinstance(value, dict):
            config[key] = update_config_with_env_vars(value)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var, None)
    return config
