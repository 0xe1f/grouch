from lxml.html import clean
import html

_SANITIZER = clean.Cleaner(
    allow_tags=[
        "a",
        "address",
        "em",
        "strong",
        "b",
        "i",
        "big",
        "small",
        "sub",
        "sup",
        "cite",
        "code",
        "ol",
        "ul",
        "li",
        "dl",
        "lh",
        "dt",
        "dd",
        "p",
        "table",
        "tr",
        "th",
        "td",
        "pre",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "div",
        "span",
        "ins",
        "del",
        "img",
    ],
    safe_attrs_only=True,
)
_CLEANER = clean.Cleaner(
    allow_tags=[''],
)

def sanitize_html(content: str) -> str:
    return _SANITIZER.clean_html(content)

def extract_text(content: str, max_len: int=None) -> str:
    content = _CLEANER.clean_html(content)
    content = _strip_bookend_tags(content)

    if max_len and len(content) > max_len:
        content = content[:max_len]

    return html.unescape(content)

def _strip_bookend_tags(content: str) -> str:
    # Remove the div tags Cleaner inserts
    if content.startswith("<div>"):
        content = content[5:]
    if content.endswith("</div>"):
        content = content[:-6]

    return content
