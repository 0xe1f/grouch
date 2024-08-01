#!/bin/bash

if [ ! -d venv ]; then
    python3 -m venv venv
    source venv/bin/activate
fi
pip install -r requirements.txt
