from store.connection import Connection
from store import views

def find_tags_by_user(conn: Connection, user_id: str, limit: int=40):
    options = {
        "start_key": [user_id],
        "end_key": [user_id, {}],
        "reduce": True,
        "group": True,
    }
    matches = []
    for item in conn.db.view(views.TAGS_BY_USER, **options):
        if item.key and len(item.key) >= 2:
            matches.append(item.key[1])
        if len(matches) >= limit:
            break

    return matches
