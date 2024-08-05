from datatype.article import Article
from datatype.entry_content import EntryContent
from web.ext_type.json_object import JsonObject

class PublicArticle(JsonObject):

    # 	Media []*EntryMedia   `datastore:"-" json:"media,omitempty"`

    def __init__(self, article: Article|None=None, entry: EntryContent|None=None, source: dict={}):
        super().__init__(source)
        if article:
            self.set_prop("id", article.id)
            self.set_prop("properties", article.props)
            self.set_prop("tags", article.tags)
            self.set_prop("source", article.subscription_id)
        if entry:
            self.set_prop("link", entry.link)
            self.set_prop("title", entry.title)
            self.set_prop("author", entry.author)
            self.set_prop("summary", entry.text_summary)
            self.set_prop("content", entry.text_body)
            self.set_prop("published", entry.published)

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @property
    def author(self) -> str:
        return self._doc.get("author")

    @property
    def summary(self) -> str:
        return self._doc.get("summary")

    @property
    def body(self) -> str:
        return self._doc.get("content")

    @property
    def tags(self) -> list[str]:
        return self._doc.get("tags")

    @property
    def props(self) -> list[str]:
        return self._doc.get("properties")

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @property
    def subscription_id(self) -> str:
        return self._doc.get("source")
