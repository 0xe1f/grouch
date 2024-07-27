from common import format_iso
from time import struct_time
from store import Connection

def stale_feeds(conn: Connection, stale_start: struct_time=None):
    batch_limit = 40
    options = {
        "descending": True
    }
    if stale_start:
        options.update(startkey=format_iso(stale_start))

    z = conn.db.iterview("maint/updated-feeds", batch_limit, **options)
    for y in z:
        yield {
            "id": y["id"],
            "url": y["value"],
        }
