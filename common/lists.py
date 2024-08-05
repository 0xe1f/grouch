from typing import TypeVar

T = TypeVar("T", bound=object)

def first_or_none(items: list[T]) -> T|None:
    return next(iter(items), None)
