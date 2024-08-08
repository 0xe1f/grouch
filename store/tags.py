from store.connection import Connection

def find_tags_by_user(conn: Connection, user_id: str):
    options = {
        "start_key": [user_id],
        "end_key": [user_id, {}],
        "reduce": True,
        "group": True,
    }
    for item in conn.db.view("maint/tags-by-user", **options):
        if item.key and len(item.key) >= 2:
            yield item.key[1]
