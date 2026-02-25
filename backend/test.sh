#!/bin/bash

# Ensure we're in the backend directory
cd "$(dirname "$0")" || exit 1

# Export PYTHONPATH to include the current directory so Python can find 'src'
export PYTHONPATH=.

echo "Running backend unit tests..."
pytest tests/ -v
