import time

def format_iso(tuple):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", tuple)

def now_in_iso():
    return format_iso(time.gmtime())
