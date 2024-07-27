class Category:

    def __init__(self, title=None):
        self.items = []
        self.title = title

    def add(self, item):
        self.items.append(item)

    def __repr__(self):
        return str(self.__dict__)
