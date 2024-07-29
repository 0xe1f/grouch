class DatabaseConfig:


    def __init__(self, **item):
        self.__dict__.update(item)

        if not self.port:
            self.port = 5984


    def validate(self):
        if not self.name:
            raise ValueError("Missing database name")
        if not self.username:
            raise ValueError("Missing database username")
        if not self.password:
            raise ValueError("Missing database password")
        if not self.host:
            raise ValueError("Missing database host")
        if not self.port:
            raise ValueError("Missing database port")
