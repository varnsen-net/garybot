#!/bin/sh

# set the PYTHONPATH to the current directory
export PYTHONPATH=$(pwd)

# start the client
uv run ./src/main.py
