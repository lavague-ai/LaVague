# Installation

## Installing the latest release

You can install the latest release of `lavague` with the following command:

`pip install lavague`

This will install a core bundle of lavague packages required for usage of lavague with default configurations - you can see which packages are included in this bundle in out `pyproject.toml` file at the root of our repo.

!!! note "Optional lavague packages"

    If you want to use packages not included in our default bundle, you will need to manually install the relevant package.

    For example, if you want to use a non-default context such as the Gemini context. You would need to run:

    ```bash
    pip install lavague.contexts.gemini
    ```

## Installing from source

If you want to install from source, you can do so by cloning the repo and running the following command from the root of the repo:

```bash
pip install -e .
```

## Dev environment

If you plan to modify local files, we recommend you follow our [dev environment guidelines](../contributing/general.md)