import couchdb

class Connection:

    def __init__(self, db_name: str):
        self.db_name = db_name

    def connect(self, user: str, pword: str, host: str, port: int):
        self.server = couchdb.Server(f"http://{user}:{pword}@{host}:{port}/")
        self.initialize()

    def initialize(self):
        # Create db
        if self.db_name not in self.server:
            self.db = self.server.create(self.db_name)
        else:
            self.db = self.server[self.db_name]
        
        # Create views
        self.create_view(
            "maint",
            "updated-feeds",
            map_fn="""
                function (doc) {
                    if (doc.doc_type == 'feed') {
                        emit(doc.updated, doc.content.url);
                    }
                }
            """
        )
        self.create_view(
            "maint",
            "users-by-email",
            map_fn="""
                function (doc) {
                    if (doc.doc_type == 'user') {
                        emit(doc.content.email_address, null);
                    }
                }
            """,
            reduce_fn="_count"
        )

    def create_view(self, design_doc: str, name: str, map_fn: str, reduce_fn: str=None) -> bool:
        id = f"_design/{design_doc}"
        if id in self.db:
            return False

        view_dict = { "map": map_fn }
        if reduce_fn:
            view_dict["reduce"] = reduce_fn

        self.db[id] = {
            "_id": f"_design/{design_doc}",
            "views": { name: view_dict },
            "language": "javascript",
            "options": { "partitioned": False }
        }

        return True
