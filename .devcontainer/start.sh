#!/bin/bash

set -e

cd $HOME/LaVague/lavague-core
poetry install
cd ..
poetry install
poetry shell