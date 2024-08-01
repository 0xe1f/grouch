from datatype.article import Article
from datatype.entry_content import EntryContent

class PublicArticle:

    # 	Media []*EntryMedia   `datastore:"-" json:"media,omitempty"`

    def __init__(self, article: Article, entry: EntryContent):
        self._doc = {}
        self.id = article.id
        self.link = entry.link
        self.title = entry.title
        self.author = entry.author
        self.summary = entry.text_summary
        self.body = entry.text_body
        self.props = article.props
        self.tags = article.tags
        self.published = entry.published
        self.subscription_id = article.subscription_id

    @property
    def id(self) -> str:
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def link(self) -> str:
        return self._doc.get("link")

    @link.setter
    def link(self, val: str):
        self._doc["link"] = val

    @property
    def title(self) -> str:
        return self._doc.get("title")

    @title.setter
    def title(self, val: str):
        self._doc["title"] = val

    @property
    def author(self) -> str:
        return self._doc.get("author")

    @author.setter
    def author(self, val: str):
        self._doc["author"] = val

    @property
    def summary(self) -> str:
        return self._doc.get("summary")

    @summary.setter
    def summary(self, val: str):
        self._doc["summary"] = val

    @property
    def body(self) -> str:
        return self._doc.get("content")

    @body.setter
    def body(self, val: str):
        self._doc["content"] = val

    @property
    def tags(self) -> list[str]:
        return self._doc.get("tags")

    @tags.setter
    def tags(self, val: list[str]):
        self._doc["tags"] = val

    @property
    def props(self) -> list[str]:
        return self._doc.get("properties")

    @props.setter
    def props(self, val: list[str]):
        self._doc["properties"] = val

    @property
    def published(self) -> str:
        return self._doc.get("published")

    @published.setter
    def published(self, val: str):
        self._doc["published"] = val

    @property
    def subscription_id(self) -> str:
        return self._doc.get("source")

    @subscription_id.setter
    def subscription_id(self, val: str):
        self._doc["source"] = val

    def doc(self):
        return self._doc
