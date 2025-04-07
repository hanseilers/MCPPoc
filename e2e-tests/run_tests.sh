#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install --with-deps chromium

# Run the tests
python -m pytest test_simple_client.py -v
