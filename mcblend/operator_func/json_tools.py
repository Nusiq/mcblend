'''
Utility functions for working with JSON and dictionaries.
'''
from __future__ import annotations

import json
from typing import Iterable, List, Optional, Union, Dict, Any
from collections import UserDict, UserList

from .exception import InvalidDictPathException

def get_vect_json(arr: Iterable) -> List[float]:
    '''
    Changes the iterable of numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.

    :param arr: an iterable of numbers.
    '''
    result = [round(i, 3) for i in arr]
    for i, _ in enumerate(result):
        if result[i] == -0.0:
            result[i] = 0.0
    return result


def get_path(
        jsonable: Optional[Union[Dict, List, str, float, int, bool]],
        path: List[Union[str, int]]
    ) -> Optional[Any]:
    '''
    Returns the object from given JSON path.
    Raises InvalidDictPathException when path is invalid.

    :param jsonable: An object which can be saved in JSON format
    :param path: a path to target object
    :returns: the target object.
    '''
    curr_obj = jsonable
    for path_item in path:
        try:
            curr_obj = curr_obj[path_item]  # type: ignore
        except (LookupError, TypeError) as e:
            raise InvalidDictPathException() from e
    return curr_obj


class CompactEncoder(json.JSONEncoder):
    '''
    JSONEncoder which can encode JSON in compact yet still readable form.
    Additionally it can encode UserDict and UserList from collections.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indent = -1
        self.respect_indent = True

    @staticmethod
    def _is_primitive(obj):
        return isinstance(obj, (int, bool, str, float))

    def encode(self, obj):
        '''
        Return a JSON string representation of a Python data structure.

        .. code-block:: python

            >>> CompactEncoder().encode({"foo": ["bar", "baz"]})
            '{\\n\\t"foo": ["bar", "baz"]\\n}'
        '''
        # pylint: disable=arguments-differ
        return ''.join(self.iterencode(obj))

    def iterencode(self, obj):
        # pylint: disable=W0221, R0912
        '''
        Encode the given object and yield each string representation line by
        line.

        .. code-block:: python

            >>> item = {"foo": ["bar", "baz"]}
            >>> ''.join(list(CompactEncoder().iterencode(item))) == \\
            ... CompactEncoder().encode(item)
            True
        '''
        self.indent += 1
        if self.respect_indent:
            ind = self.indent*'\t'
        else:
            ind = ''
        if isinstance(obj, (dict, UserDict)):
            if not obj:  # if empty
                yield f"{ind}{{}}"
            else:
                body = []
                for k, v in obj.items():
                    body.extend([
                        f'{j[:self.indent]}"{k}": {j[self.indent:]}'
                        for j in self.iterencode(v)
                    ])
                body_str = ",\n".join(body)
                yield (
                    f'{ind}{{\n'
                    f'{body_str}\n'
                    f'{ind}}}'
                )
        elif isinstance(obj, (list, tuple, UserList)):
            primitive_list = True
            for i in obj:
                if not self._is_primitive(i):
                    primitive_list = False
                    break
            if primitive_list:
                body = []
                self.respect_indent = False
                for i in obj:
                    body.extend(self.iterencode(i))
                self.respect_indent = True
                yield f'{ind}[{", ".join(body)}]'
            else:
                body = []
                for i in obj:
                    body.extend(self.iterencode(i))
                body_str = ",\n".join(body)
                yield (
                    f'{ind}[\n'
                    f'{body_str}\n'
                    f'{ind}]'
                )
        elif self._is_primitive(obj):
            if isinstance(obj, str):
                yield f'{ind}"{str(obj)}"'
            elif isinstance(obj, float) and obj.is_integer():
                yield f'{ind}{str(int(obj))}'
            else:
                yield f'{ind}{str(obj).lower()}'
        elif obj is None:
            yield f'{ind}null'
        else:
            raise TypeError('Object of type set is not JSON serializable')
        self.indent -= 1
