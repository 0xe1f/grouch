from common import first_or_none
from store import find_folders_by_id
from store import find_sub_ids_by_folder
from store import BulkUpdateQueue
from store import Connection
from tasks.subscriptions import remove_subscriptions
from time import time
import logging

def delete_folder(conn: Connection, folder_id: str):
    start_time = time()
    all_subscriptions_removed = True

    with BulkUpdateQueue(conn, track_ids=False) as bulk_q:
        if sub_ids := find_sub_ids_by_folder(conn, folder_id):
            if not remove_subscriptions(bulk_q, *sub_ids):
                all_subscriptions_removed = False
                logging.warning(f"Not all subscriptions were removed")

        if all_subscriptions_removed:
            # Don't remove folder if one or more subs were left
            if folder := first_or_none(find_folders_by_id(conn, folder_id)):
                folder.mark_deleted()
                bulk_q.enqueue_flex(folder)
            else:
                logging.warning(f"No folder with id {folder_id}")

    logging.info(f"Delete folder {folder_id}: {bulk_q.written_count}/{bulk_q.enqueued_count} objects written ({time() - start_time:.2}s)")
