from common import format_iso
from couchdb.http import ResourceConflict
from datatype import User
from store import Connection
from time import gmtime
import logging


def create_user(conn: Connection, user: User) -> bool:
    item_id = user_id(user)
    if item_id in conn.db:
        logging.error(f"User with id {item_id} already exists")
        return False
    elif email_address_count(conn, user.email_address) > 0:
        logging.error(f"User with email address {user.email_address} already exists")
        return False

    doc = {
        "_id": item_id,
        "doc_type": "user",
        "content": user.doc(),
        "updated": format_iso(gmtime()),
    }

    try:
        new_id, _ = conn.db.save(doc)
    except ResourceConflict as e:
        logging.exception(f"Error writing user {item_id}", e)
        return False

    # Ensure we didn't end up writing multiple addresses
    new_count = email_address_count(conn, user.email_address)
    if new_count > 1:
        logging.warning(f"There are {new_count} instances of users with address {user.email_address}")
        # Delete dupe account
        del conn.db[new_id]
        return False

    return True


def email_address_count(conn: Connection, email_address: str) -> bool:
    result = conn.db.view("maint/users-by-email", reduce=True, group=True, limit=1)
    next_item = next(result[email_address].__iter__(), None)

    if next_item:
        return next_item.value
    else:
        return 0


def user_id(user: User) -> str:
    return f"user::{user.username}"
