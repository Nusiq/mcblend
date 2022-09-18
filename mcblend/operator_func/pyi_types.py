'''
Extra types used only in the PYI files.
'''
from typing import Any, Iterator, TypeVar, Generic, Sized

T = TypeVar("T")

class CollectionProperty(Sized, Generic[T]):
    def __getitem__(self, key: Any) -> T:
        ...
    def __iter__(self) -> Iterator[T]:
        ...
    def add(self) -> T:
        ...

    def clear (self) -> None:
        ...
