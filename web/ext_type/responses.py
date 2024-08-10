from web.ext_type.article import Article
from web.ext_type.json_object import JsonObject
from web.ext_type.table_of_contents import TableOfContents

class ArticlesResponse(JsonObject):

    def __init__(self, articles: list[Article]=[], next_start: str|None=None):
        super().__init__(
            {
                "articles": [article.as_dict() for article in articles],
                "continue": next_start,
            }
        )

class CreateFolderResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class MoveSubResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class RemoveTagResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class RenameResponse(JsonObject):

    def __init__(self, toc: TableOfContents):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
            },
        )

class SetTagsResponse(JsonObject):

    def __init__(self, toc: TableOfContents, tags: list[str]):
        super().__init__(
            {
                "subscriptions": toc.as_dict(),
                "tags": tags,
            },
        )
