'''
Extra types used only in the PYI files.
'''
from typing import Any, Iterator, TypeVar, Generic, Sized, Optional
from bpy.types import Object, Mesh

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

class DataObjects(Sized):
    '''
    Fake class defined as a result of:
    >>> bpy.data.objects
    '''
    def __getitem__(self, key: Any) -> Object: ...
    def __iter__(self) -> Iterator[Object]: ...
    def new(self, name: str, object_data: Optional[Mesh] = None) -> Object: ...