class Subscription:

    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url

    def __repr__(self):
        return str(self.__dict__)
