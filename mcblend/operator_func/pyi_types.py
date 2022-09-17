'''
Extra types used only in the PYI files.
'''
from typing import Any, Iterator, TypeVar, Generic

T = TypeVar("T")

class CollectionProperty(Generic[T]):
    def __getitem__(self, key: Any) -> T:
        ...
    def __iter__(self) -> Iterator[T]:
        ...
    def add(self) -> T:
        ...
