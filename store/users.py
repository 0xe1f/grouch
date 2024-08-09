from common import build_key
from common import now_in_iso
from couchdb.http import ResourceConflict
from datatype import User
from store.connection import Connection
import logging

def find_user_id(conn: Connection, username: str) -> str:
    item_id = build_key("user", username)
    if conn.db.get(item_id):
        return item_id

    return None

def fetch_user(conn: Connection, user_id: str) -> User:
    for item in conn.db.view("_all_docs", key=user_id, include_docs=True):
        return User(item.doc)

    return None

def create_user(conn: Connection, user: User) -> bool:
    if not user.id:
        user.id = user.build_key()
    if user.id in conn.db:
        logging.error(f"User with id {user.id} already exists")
        return False
    elif _email_address_count(conn, user.email_address) > 0:
        logging.error(f"User with email address {user.email_address} already exists")
        return False

    user.updated = now_in_iso()

    try:
        new_id, _ = conn.db.save(user.doc())
    except ResourceConflict as e:
        logging.exception(f"Error writing user {user.id}", e)
        return False

    # Ensure we didn't end up writing multiple addresses
    new_count = _email_address_count(conn, user.email_address)
    if new_count > 1:
        logging.warning(f"There are {new_count} instances of users with address {user.email_address}")
        # Delete dupe account
        del conn.db[new_id]
        return False

    return True

def _email_address_count(conn: Connection, email_address: str) -> bool:
    result = conn.db.view("maint/users_by_email", reduce=True, group=True, limit=1)
    next_item = next(result[email_address].__iter__(), None)

    if next_item:
        return next_item.value
    else:
        return 0
