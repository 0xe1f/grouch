from config import DatabaseConfig
import couchdb
import logging

_METADATA_KEY = "$store_metadata"
_METADATA_SCHEMA_VERSION = "schema_version"

_SCHEMA_VERSION_CURRENT = 1

class Connection:

    def __init__(self):
        pass

    def connect(self, config: DatabaseConfig):
        config.validate()
        self.server = couchdb.Server(f"http://{config.username}:{config.password}@{config.host}:{config.port}/")
        self.initialize(config.name)

    def initialize(self, database_name: str):
        # Create DB if necessary
        if database_name not in self.server:
            self.db = self.server.create(database_name)
        else:
            self.db = self.server[database_name]

        if _METADATA_KEY in self.db:
            metadata = self.db[_METADATA_KEY]
        else:
            metadata = {
                "_id": _METADATA_KEY,
                _METADATA_SCHEMA_VERSION: 0
            }

        stored_version = metadata[_METADATA_SCHEMA_VERSION]
        if stored_version < _SCHEMA_VERSION_CURRENT:
            logging.info(f"Upgrading schema from version {stored_version} to {_SCHEMA_VERSION_CURRENT}")
            self.update_schema(stored_version)
            metadata[_METADATA_SCHEMA_VERSION] = _SCHEMA_VERSION_CURRENT
            self.db.save(metadata)

    def update_schema(self, from_ver: int):
        design_doc = self.get_design_doc("maint")
        self.add_views(
            design_doc,
            updated_feeds={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'feed') {
                            emit(doc.updated);
                        }
                    }
                """
            },
            users_by_email={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'user') {
                            emit(doc.email_address);
                        }
                    }
                """,
                "reduce": "_count"
            },
            feeds_by_url={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'feed') {
                            emit(doc.feed_url);
                        }
                    }
                """
            },
            folders_by_user={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'folder') {
                            emit(doc.user_id);
                        }
                    }
                """
            },
            entries_by_feed={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'entry') {
                            emit([doc.feed_id, doc.entry_uid]);
                        }
                    }
                """
            },
            entries_by_feed_updated={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'entry') {
                            emit([doc.feed_id, doc.updated]);
                        }
                    }
                """
            },
            subs_by_user={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'sub') {
                            emit([ doc.user_id, doc.last_synced ], { "feed_id": doc.feed_id, "last_sync": doc.last_synced });
                        }
                    }
                """
            },
            subs_by_folder={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'sub' && doc.folder_id) {
                            emit(doc.folder_id);
                        }
                    }
                """
            },
            articles_by_user={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article') {
                            emit([doc.user_id, doc.published, doc.updated]);
                        }
                    }
                """
            },
            articles_by_sub={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article') {
                            emit([doc.subscription_id, doc.published, doc.updated]);
                        }
                    }
                """
            },
            articles_by_sub_unread={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article' && doc.props.includes('unread')) {
                            emit([doc.subscription_id, doc.published, doc.updated]);
                        }
                    }
                """
            },
            articles_by_folder={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article' && doc.folder_id) {
                            emit([doc.folder_id, doc.published, doc.updated]);
                        }
                    }
                """
            },
            articles_by_folder_unread={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article' && doc.folder_id && doc.props.includes('unread')) {
                            emit([doc.folder_id, doc.published, doc.updated]);
                        }
                    }
                """
            },
            articles_by_prop={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article') {
                            doc.props.forEach((prop) => {
                                emit([doc.user_id, prop, doc.published, doc.updated])
                            });
                        }
                    }
                """
            },
            articles_by_tag={
                "map": """
                    function (doc) {
                        if (doc.doc_type == 'article') {
                            doc.tags.forEach((tag) => {
                                emit([doc.user_id, tag, doc.published, doc.updated])
                            });
                        }
                    }
                """
            },
            tags_by_user={
                "map": """
                    function (doc) {
                        doc.tags.forEach((tag) => {
                            emit([doc.user_id, tag])
                        });
                    }
                """,
                "reduce": "_count"
            },
        )
        self.save_design_doc(design_doc)

    def get_design_doc(self, design_doc_name: str):
        id = f"_design/{design_doc_name}"
        if id in self.db:
            return self.db[id]
        else:
            return {
                "_id": id,
                "views": {},
                "language": "javascript",
                "options": { "partitioned": False }
            }

    def save_design_doc(self, design_doc: dict):
        self.db.save(design_doc)

    def add_views(self, design_doc: dict, **kwargs):
        for key, value in kwargs.items():
            design_doc["views"][key] = value
