#!/bin/sh

# set the PYTHONPATH to the current directory
export PYTHONPATH=$(pwd)

# dirs
mkdir -p data/odds
mkdir -p data/user-logs

# start the client
uv run ./src/main.py
