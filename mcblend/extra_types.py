from typing import TYPE_CHECKING, Any, Iterator, TypeVar, Generic

import bpy

T = TypeVar("T")

class CollectionPropertyAnnotation(Generic[T]):
    def __getitem__(self, key: Any) -> T:
        ...
    def __iter__(self) -> Iterator[T]:
        ...
    def add(self) -> T:
        ...