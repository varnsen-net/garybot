#!/bin/sh

CWD=$(pwd)

# set the PYTHONPATH to the current directory
export PYTHONPATH=$CWD:$PYTHONPATH

# start the client
uv run ./src/main.py
