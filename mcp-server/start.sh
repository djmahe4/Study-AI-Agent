#!/bin/bash
# Use venv if it exists
VENV_DIR="../venv"
if [ -d "$VENV_DIR" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python"
else
    # Try local venv too
    VENV_DIR="venv"
    if [ -d "$VENV_DIR" ]; then
        PYTHON_BIN="$VENV_DIR/bin/python"
    else
        PYTHON_BIN="python"
    fi
fi

export PYTHONPATH=$PYTHONPATH:$(pwd)
$PYTHON_BIN -m uvicorn server:app --reload --port 8765
