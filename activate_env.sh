#!/bin/bash
# Activate virtual environment and show status
# Usage: source activate_env.sh

# Activate the virtual environment
source venv/bin/activate

# Show confirmation
echo "✓ Virtual environment activated!"
echo "Python location: $(which python)"
echo "Python version: $(python --version)"
echo ""
echo "To deactivate, type: deactivate"
