#!/bin/sh
set -e  # Exit if any command fails

# Install pdoc3 for generating Python API documentation
pip install lavague pdoc3

# Generate HTML documentation
pdoc --html --skip-errors --template-dir docs/pdoc_template -o docs/docs/ lavague-core/lavague/core --force
