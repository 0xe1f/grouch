import time

def format_iso(tuple):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", tuple)
