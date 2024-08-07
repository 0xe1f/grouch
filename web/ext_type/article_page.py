from web.ext_type.json_object import JsonObject
from web.ext_type.public_article import PublicArticle

class ArticlePage(JsonObject):

    def __init__(self, source: dict={}, next_start: str|None=None, articles: list[PublicArticle]=[]):
        super().__init__(source)
        self.set_prop("articles", [article.as_dict() for article in articles])
        if next_start:
            self.set_prop("continue", next_start)

    @property
    def articles(self) -> list[PublicArticle]:
        return [PublicArticle(article) for article in self._doc.get("articles")]

    @property
    def next_start(self) -> str:
        return self._doc.get("continue")
