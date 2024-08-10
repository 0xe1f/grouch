from typing import TypeVar

T = TypeVar("T", bound=object)

def first_or_none(items: list[T]) -> T|None:
    return next(iter(items), None)

def first_index(items: list[T], value: T) -> int:
    return next((ix for ix in range(len(items)) if items[ix] == value), -1)
