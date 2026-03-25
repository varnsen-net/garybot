#!/bin/sh

CWD=$(pwd)

# set the PYTHONPATH to the current directory
export PYTHONPATH=$CWD:$PYTHONPATH

# dirs
mkdir -p $CWD/data/user-logs
mkdir -p $CWD/data/odds

# start the client
uv run ./src/main.py
