#!/bin/bash

MATCH_PATTERN=test_*.py

if [ -n "$1" ]; then
    MATCH_PATTERN="$1"
fi

python -m unittest discover -v -s tests -p $MATCH_PATTERN
