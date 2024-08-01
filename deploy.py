#!/usr/bin/env python3

import argparse
import subprocess

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-host", "--host", help="deployment host", required=True)
args = arg_parser.parse_args()

subprocess.call([
    'rsync',
    '-avrL',
    '--delete',
    '--exclude', '.*',
    '--exclude', 'venv',
    '--exclude', '*.yaml.example',
    '--exclude', '__pycache__',
    f'.',
    f'{args.host}:grouch'
])
