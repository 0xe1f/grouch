from config import DatabaseConfig
import couchdb

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

        # Create views
        self.create_views(
            "maint",
            {
                "updated-feeds": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'feed') {
                                emit(doc.updated, null);
                            }
                        }
                    """
                },
                "users-by-email": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'user') {
                                emit(doc.email_address, null);
                            }
                        }
                    """,
                    "reduce": "_count"
                },
                "feeds-by-url": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'feed') {
                                emit(doc.feed_url, null);
                            }
                        }
                    """
                },
                "folders-by-user": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'folder') {
                                emit(doc.content.user_id, doc.content.title);
                            }
                        }
                    """
                },
                "entries-by-feed-id": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'entry') {
                                emit([doc.feed_id, doc.entry_uid], null);
                            }
                        }
                    """
                },
                "entries-by-feed-updated": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'entry') {
                                emit([doc.feed_id, doc.updated], null);
                            }
                        }
                    """
                },
                "sub-last-synced-by-user": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'sub') {
                                emit([ doc.user_id, doc.last_synced ], { "feed_id": doc.feed_id, "last_sync": doc.last_synced });
                            }
                        }
                    """
                },
                "articles-by-user": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'article') {
                                emit([doc.user_id, doc.published, doc.updated], null);
                            }
                        }
                    """
                },
                "articles-by-sub": {
                    "map": """
                        function (doc) {
                            if (doc.doc_type == 'article') {
                                emit([doc.subscription_id, doc.published, doc.updated], null);
                            }
                        }
                    """
                },
            },
        )

    def create_views(self, design_doc: str, content: str) -> bool:
        id = f"_design/{design_doc}"
        if id in self.db:
            return False

        self.db[id] = {
            "_id": f"_design/{design_doc}",
            "views": content,
            "language": "javascript",
            "options": { "partitioned": False }
        }

        return True
