'''
Provides decoder for JSON with comments and helps you navigate
objects loaded into Python from JSON files.

This submodule is used by in :code:`bedrock_packs` to get any information
from JSON files but it's also useful to easily navigate the content of JSON
with writing as little code as possible.

The JSON navigation is provided by two classes :class:`JsonWalker` and
:class:`JsonSplitWalker`. They use the similar syntax to pathlib Path
objects to create paths but they evaluate the paths on the go and additionally
they let you crete split paths (:class:`JsonSplitWalker`) to access multiple
parts of the JSON at the same time.

Here are some code examples:

.. code-block:: python

    from bedrock_packs.json import JsonWalker

    with open('file.json', 'r') as f:
        walker = JsonWalker.load(f)

    # the content of the file
    print(walker.data)
    # output:
    # {'a': 1, 'b': [{'x': 1, 'y': 2}, {'x': 4, 'y': 5}], 
    # 'c': {'c1': {'x': 11, 'y': 22}, 'c2': {'x': 44, 'y': 55}}}

    # the value of 'a' property
    print((walker / 'a').data)
    # output:
    # 1

    # the value of any list element from 'b' property
    for i in (walker / 'b' // int).data:
        print(i.data)
    # output:
    # {'x': 1, 'y': 2}
    # {'x': 4, 'y': 5}

    # the 'x' value of any item (from list or object) from any object that
    # matches the '[a-z]' regex
    for i in (walker // '[a-z]' // None / 'x').data:
        print(i.data)
    # output:
    # 1
    # 4
    # 11
    # 44

    # Creating JSON paths using create_path method
    data = JsonWalker({})

    new_path = data /'a' / 'b'
    new_path.create_path("Hello")
    # data:
    # {"a": {"b": "Hello"}}

    new_path = data / 'c' / 3
    new_path.create_path("Test", empty_list_item_factory=lambda: "abc")
    # data:
    # {"a": {"b": "Hello"}, "c": ["abc", "abc", "abc", "Test"]}
'''
from __future__ import annotations
from typing import Callable, Dict, Generic, IO, Iterator, List, NewType, Tuple, Type, TypeVar, Union, Optional
import re
import json
from json import scanner, JSONDecodeError  # type: ignore
from json.decoder import WHITESPACE, WHITESPACE_STR, scanstring  # type: ignore



# JSON Decoder
FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
INLINE_COMMENT = re.compile(r'//[^\n]*\n?', FLAGS)
INLINE_COMMENT_STRING_START='//'
MULTILINE_COMMENT = re.compile(r"/[*]([^*]|([*][^/]))*[*]+/", FLAGS)
MULTILINE_COMMENT_STRING_START='/*'


def parse_object(
    s_and_end, strict, scan_once, object_hook, object_pairs_hook,
    memo=None, _w=WHITESPACE.match, _ws=WHITESPACE_STR,
    _ilcs=INLINE_COMMENT_STRING_START, _ilc=INLINE_COMMENT.match,
    _mlcs=MULTILINE_COMMENT_STRING_START, _mlc=MULTILINE_COMMENT.match
):
    '''
    Modified json.decoder.JSONObject function from standard json module
    (python 3.7.7).
    '''
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"':
        while True:  # Handle comments and whitespaces
            if nextchar in _ws:
                end = _w(s, end).end()
            elif s[end:].startswith(_ilcs):
                end = _ilc(s, end).end()
            elif s[end:].startswith(_mlcs):
                end = _mlc(s, end).end()
            else:
                break
            nextchar = s[end:end + 1]

        # Trivial empty object
        if nextchar == '}':
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        key, end = scanstring(s, end, strict)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end:end + 1] != ':':
            while True:  # Handle comments and whitespaces
                if s[end:end + 1] in _ws:
                    end = _w(s, end).end()
                elif s[end:].startswith(_ilcs):
                    end = _ilc(s, end).end()
                elif s[end:].startswith(_mlcs):
                    end = _mlc(s, end).end()
                else:
                    break
            if s[end:end + 1] != ':':
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        try:
            while True:  # Handle comments and whitespaces
                if s[end] in _ws:
                    end = _w(s, end).end()
                elif s[end:].startswith(_ilcs):
                    end = _ilc(s, end).end()
                elif s[end:].startswith(_mlcs):
                    end = _mlc(s, end).end()
                else:
                    break
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs_append((key, value))

        try:
            nextchar = s[end]
            while True:  # Handle comments and whitespaces
                if nextchar in _ws:
                    end = _w(s, end).end()
                elif s[end:].startswith(_ilcs):
                    end = _ilc(s, end).end()
                elif s[end:].startswith(_mlcs):
                    end = _mlc(s, end).end()
                else:
                    break
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)

        while True:  # Handle comments and whitespaces
            if s[end] in _ws:
                end = _w(s, end).end()
            elif s[end:].startswith(_ilcs):
                end = _ilc(s, end).end()
            elif s[end:].startswith(_mlcs):
                end = _mlc(s, end).end()
            else:
                break
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    return pairs, end


def parse_array(
    s_and_end, scan_once, _w=WHITESPACE.match, _ws=WHITESPACE_STR,
    _ilcs=INLINE_COMMENT_STRING_START, _ilc=INLINE_COMMENT.match,
    _mlcs=MULTILINE_COMMENT_STRING_START, _mlc=MULTILINE_COMMENT.match
):
    '''
    Modified json.decoder.JSONArray function from standard module json
    (python 3.7.7).
    '''
    s, end = s_and_end
    values = []
    nextchar = s[end:end + 1]
    while True:  # Handle comments and whitespaces
        if nextchar in _ws:
            end = _w(s, end).end()
        elif s[end:].startswith(_ilcs):
            end = _ilc(s, end).end()
        elif s[end:].startswith(_mlcs):
            end = _mlc(s, end).end()
        else:
            break
        nextchar = s[end:end + 1]

    # Look-ahead for trivial empty array
    if nextchar == ']':
        return values, end + 1
    _append = values.append
    while True:
        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        _append(value)
        nextchar = s[end:end + 1]

        while True:  # Handle comments and whitespaces
            if nextchar in _ws:
                end = _w(s, end).end()
            elif s[end:].startswith(_ilcs):
                end = _ilc(s, end).end()
            elif s[end:].startswith(_mlcs):
                end = _mlc(s, end).end()
            else:
                break
            nextchar = s[end:end + 1]
        end += 1

        if nextchar == ']':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)

        try:
            while True:  # Handle comments and whitespaces
                if s[end] in _ws:
                    end = _w(s, end).end()
                elif s[end:].startswith(_ilcs):
                    end = _ilc(s, end).end()
                elif s[end:].startswith(_mlcs):
                    end = _mlc(s, end).end()
                else:
                    break
        except IndexError:
            pass

    return values, end


class JSONCDecoder(json.JSONDecoder):
    '''
    JSONDecoder with support for C-style comments. Similar to JSONC files from
    Visual Studio code but without support for trailing commas.
    '''
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, *args, **kwargs)
        self.parse_object = parse_object
        self.parse_array = parse_array

        # we need to recreate the internal scan function ..
        self.scan_once = scanner.py_make_scanner(self)

    def decode(
        self, s, _w=WHITESPACE.match,
        _ws=WHITESPACE_STR,
        _ilcs=INLINE_COMMENT_STRING_START, _ilc=INLINE_COMMENT.match,
        _mlcs=MULTILINE_COMMENT_STRING_START, _mlc=MULTILINE_COMMENT.match
    ):
        idx = 0
        try:
            while True:  # Handle comments and whitespaces
                if s[idx] in _ws:
                    idx = _w(s, idx).end()
                elif s[idx:].startswith(_ilcs):
                    idx = _ilc(s, idx).end()
                elif s[idx:].startswith(_mlcs):
                    idx = _mlc(s, idx).end()
                else:
                    break
        except IndexError:
            pass
        obj, end = self.raw_decode(s, idx)
        end = _w(s, end).end()
        if end != len(s):
            raise JSONDecodeError("Extra data", s, end)
        return obj

# JSON Encoder
class CompactEncoder(json.JSONEncoder):
    '''
    JSONEncoder which is a compromise between compact and multiline
    formatting from standard python json module. Creates relatively compact
    file which is also easy to read.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indent = -1
        self.respect_indent = True

    def _is_primitive(self, obj):
        return isinstance(obj, (int, bool, str, float))

    def encode(self, obj):
        '''
        Return a JSON string representation of a Python data structure.

        Example:

        >>> CompactEncoder().encode({"foo": ["bar", "baz"]})
        '{\\n\\t"foo": ["bar", "baz"]\\n}'
        '''
        return ''.join([i for i in self.iterencode(obj)])

    def iterencode(self, obj):
        '''
        Encode the given object and yield each string representation line by
        line.

        Example:

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
        if isinstance(obj, dict):
            if len(obj) == 0:
                yield f"{ind}{{}}"
            else:
                body = []
                if self.sort_keys is True:
                    obj_iter = sorted(iter(obj.items()))
                else:
                    obj_iter = obj.items()
                for k, v in obj_iter:
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
        elif isinstance(obj, (list, tuple)):
            primitive_list = True
            for i in obj:
                if not self._is_primitive(i):
                    primitive_list = False
                    break
            if primitive_list:
                body = []
                self.respect_indent = False
                for i in obj:
                    body.extend([j for j in self.iterencode(i)])
                self.respect_indent = True
                yield f'{ind}[{", ".join(body)}]'
            else:
                body = []
                for i in obj:
                    body.extend([j for j in self.iterencode(i)])
                body_str = ",\n".join(body)
                yield (
                    f'{ind}[\n'
                    f'{body_str}\n'
                    f'{ind}]'
                )
        elif self._is_primitive(obj):
            if isinstance(obj, str):
                obj_str = obj.replace("\\", "\\\\").replace('"', '\\"')
                yield f'{ind}"{obj_str}"'
            else:
                yield f'{ind}{str(obj).lower()}'
        elif obj is None:
            yield f'{ind}null'
        else:
            raise TypeError('Object of type set is not JSON serializable')
        self.indent -= 1

# JSON path

## Type definitions
JSON = Union[Dict, List, str, float, int, bool, None]
JSON_KEY = Union[str, int]
JSON_SPLIT_KEY = Union[str, Type[int], Type[str], None, type(Ellipsis)]
JSON_WALKER_DATA = Union[Dict, List, str, float, int, bool, None, Exception]

class JsonWalker:
    '''
    Safe access to data accessed with json.load without risk of exceptions.
    '''
    def __init__(
            self, data: JSON_WALKER_DATA, *,
            parent: Optional[JsonWalker]=None,
            parent_key: Optional[JSON_KEY]=None):
        if not isinstance(
                data, (Exception, dict, list, str, float, int, bool, type(None))):
            raise ValueError('Input data is not JSON.')
        self._data: JSON_WALKER_DATA = data
        self._parent = parent
        self._parent_key = parent_key

    @property
    def parent(self) -> JsonWalker:
        '''
        The :class:`JsonWalker` which created this instance of
        :class:`JsonWalker` with :code:`__truediv__` or :code:`__floordiv__` .

        :rises: :class:`KeyError` when this :class:`JsonWalker` is a root
            object.
        '''
        if self._parent is None:
            raise KeyError("You can't get parent of the root object.")
        return self._parent

    @property
    def parent_key(self) -> JSON_KEY:
        '''
        The JSON key used to access this :class:`JsonWalker` from parent
        :class:`JsonWalker` .

        :rises: :class:`KeyError` when this :class:`JsonWalker` is a root
            object
        '''
        if self._parent_key is None:
            raise KeyError("You can't get parent of the root object.")
        return self._parent_key

    @staticmethod
    def loads(json_text: Union[str, bytes], **kwargs) -> JsonWalker:
        '''
        Create :class:`JsonWalker` from string with :code:`json.loads()` .

        :rises: Any type of exception risen by :code:`json.loads()` function
            (:class:`ValueError`).
        '''
        data = json.loads(json_text, **kwargs)
        return JsonWalker(data)

    @staticmethod
    def load(json_file: IO, **kwargs) -> JsonWalker:
        '''
        Create :class:`JsonWalker` from file input with :code:`json.load()` .

        :rises: Any type of exception risen by :code:`json.load()` function
            (:class:`ValueError`).
        '''
        data = json.load(json_file, **kwargs)
        return JsonWalker(data)

    @property
    def data(self) -> JSON_WALKER_DATA:
        return self._data

    @data.setter
    def data(self, value: JSON):
        '''
        The part of the JSON file related to this :class:`JsonWalker`.
        '''
        if self._parent is not None:
            self.parent.data[  # type: ignore
                self.parent_key  # type: ignore
            ] = value
        self._data = value

    def create_path(
        self, data: JSON, *,
        exists_ok=True,
        can_break_data_structure=True,
        can_create_empty_list_items=True,
        empty_list_item_factory: Optional[Callable[[], JSON]]=None):
        '''
        Creates path to the part of Json file pointed by this JsonWalker.
        
        :param data: the data to put at the end of the path.
        :param exists_ok: if False, the ValueError will be risen if the path
            to this item already exists.
        :param can_break_data_structure: if True than the function will be able
            to replace certain existing paths with dicts or lists. Example - 
            if path "a"/"b"/"c" points at integer, creating path
            "a"/"b"/"c"/"d" will replace this integer with a dict in order to
            make "d" a valid key. Setting this to false will cause a KeyError
            in this situation.
        :param can_create_empty_list_items: enables filling up the lists in
            JSON with values produced by the empty_list_item_factory in order
            to match the item index specified in the path. Example - if you
            specify a path to create "a"/5/"c" but the list at "a" path only
            has 2 items, then the function will create additional item so
            the 5th index can be valid.
        :param empty_list_item_factory: a function used to create items for
            lists in order to make indices specified in the path valid (see
            can_create_empty_list_items function parameter). If this value
            is left as None than the lists will be filled with null values.
        '''
        if self.exists:
            if exists_ok:
                return
            else:
                raise ValueError("Path already exists")
        if empty_list_item_factory == None:
            def empty_list_item_factory():
                return None
        curr_item = self.root
        path = self.path
        for key in path:
            if isinstance(key, str):  # key is a string data must be a dict
                if not isinstance(curr_item.data, dict):
                    if not can_break_data_structure:
                        raise KeyError(key)
                    else:
                        curr_item.data = {}
                if key not in curr_item.data:
                    can_break_data_structure = True  # Creating new data
                curr_item = curr_item / key
            elif isinstance(key, int):  # key is an int data must be a list
                if key < 0:
                    raise KeyError(key)
                if not isinstance(curr_item.data, list):
                    if not can_break_data_structure:
                        raise KeyError(key)
                    else:
                        curr_item.data = []
                if len(curr_item.data)-1 < key:
                    if not can_create_empty_list_items:
                        raise KeyError(key)
                    else:
                        curr_item.data += [
                            empty_list_item_factory()
                            for _ in range(1+key-len(curr_item.data))
                        ]
                        can_break_data_structure = True  # Creating new data
                curr_item = curr_item / key
            else:
                raise KeyError(key)
        self._parent = curr_item.parent
        self._parent_key = curr_item.parent_key
        self.data = data

    @property
    def exists(self) -> bool:
        '''
        Returns true if path to this item already exists.
        '''
        keys: List[JSON_KEY] = []
        root = self
        try:
            while True:
                keys.append(root.parent_key)
                root = root.parent
        except KeyError:
            pass
        keys = tuple(reversed(keys))
        root_data = root.data
        try:
            for key in keys:
                root_data = root_data[key]
        except:
            return False
        return True

    @property
    def root(self) -> JsonWalker:
        '''
        The root object of this JSON file.
        '''
        root = self
        try:
            while True:
                root = root.parent
        except KeyError:
            pass
        return root

    @property
    def path(self) -> Tuple[JSON_KEY, ...]:
        '''
        Full JSON path to this :class:`JsonWalker` starting from the root of
        the JSON file (loaded recursively from JSON parents).
        '''
        result: List[JSON_KEY] = []
        parent = self
        try:
            while True:
                result.append(parent.parent_key)
                parent = parent.parent
        except KeyError:
            pass
        return tuple(reversed(result))

    def __truediv__(self, key: JSON_KEY) -> JsonWalker:
        '''
        Try to access next object in the JSON path. Returns :class:`JsonWalker`
        with the next object in JSON path or with an exception if the path is
        invalid. The exception is not risen, it becomes the data of returned
        :class:`JsonWalker`.

        :param key: a json key (list index or object field name)
        '''
        try:
            return JsonWalker(
                self.data[key],  # type: ignore
                parent=self, parent_key=key)
        except Exception as e:  # index out of list bounds
            return JsonWalker(e, parent=self, parent_key=key)

    def __floordiv__(self, key: JSON_SPLIT_KEY) -> JsonSplitWalker:
        '''
        Access multiple objects from this :class:`JsonWalker` at once. Return
        :class:`JsonSplitWalker`.

        :param key: :code:`str` (any item from dictionary), :code:`int` (any
            item from listregular expression), regular expression (matches
            dictionary keys), :code:`None` (any item from dictionary or list),
            or :code:`Ellipsis` / :code:`...` (access to all list items if
            current path points at list or skip this step and return
            JsonSplitWalker with only current JsonWalker).

        :raises:
            :class:`TypeError` - invalid input data type

            :class:`re.error` - invlid regular expression.
        '''
        # ANYTHING
        if key is None:
            if isinstance(self.data, dict):
                return JsonSplitWalker([
                    JsonWalker(v, parent=self, parent_key=k)
                    for k, v in self.data.items()
                ])
            elif isinstance(self.data, list):
                return JsonSplitWalker([
                    JsonWalker(v, parent=self, parent_key=i)
                    for i, v in enumerate(self.data)
                ])
        # ANY LIST ITEM
        elif key is int:
            if isinstance(self.data, list):
                return JsonSplitWalker([
                    JsonWalker(v, parent=self, parent_key=i)
                    for i, v in enumerate(self.data)
                ])
        # ANY DICT ITEM
        elif key is str:
            if isinstance(self.data, dict):
                return JsonSplitWalker([
                    JsonWalker(v, parent=self, parent_key=k)
                    for k, v in self.data.items()
                ])
        # REGEX DICT ITEM
        elif isinstance(key, str):
            if isinstance(self.data, dict):
                result: List[JsonWalker] = []
                for k, v in self.data.items():
                    if re.fullmatch(key, k):
                        result.append(JsonWalker(
                            v, parent=self, parent_key=k))
                return JsonSplitWalker(result)
        # IF it's a list use ing key ELSE return split walker with self
        elif key is ...:
            if isinstance(self.data, list):
                return self // int
            else:
                return JsonSplitWalker([self])
        else:  # INVALID KEY TYPE
            raise TypeError(
                'Key must be a regular expression or one of the values: '
                'str, int, or None')
        # DATA DOESN'T ACCEPT THIS TYPE OF KEY
        return JsonSplitWalker([])

    def __add__(self, other: Union[JsonSplitWalker, JsonWalker]) -> JsonSplitWalker:
        '''
        Combine with :class:`JsonWalker` or  :class:`JsonSplitWalker`
        object to create :class:`JsonSplitWalker`.
        '''
        if isinstance(other, JsonWalker):
            data = [self, other]
        else:
            data = other.data + [self]
        return JsonSplitWalker(
            [i for i in data if not isinstance(i.data, Exception)])

class JsonSplitWalker:
    '''
    Multiple :class:`JsonWalker` objects grouped together. This class can be
    browse JSON file in multiple places at once.
    '''
    def __init__(self, data: List[JsonWalker]) -> None:
        self._data: List[JsonWalker] = data

    @property
    def data(self) -> List[JsonWalker]:
        '''
        The list of the :class:`JsonWalker` objects contained in this
            :class:`JSONSplitWalker`.
        '''
        return self._data

    def __truediv__(self, key: JSON_KEY) -> JsonSplitWalker:
        '''
        Execute :code:`__truediv__(key)` of every :class:`JsonWalker` of this
        object and return new :class:`JsonSplitWalker` that contains only
        thouse of the newly created :class:`JsonWalker` objects that represent
        valid JSON path.

        :param key: a json key (list index or object field name)
        '''
        result = []
        for walker in self.data:
            new_walker = walker / key
            if not isinstance(new_walker.data, Exception):
                result.append(new_walker)
        return JsonSplitWalker(result)

    def __floordiv__(self, key: JSON_SPLIT_KEY) -> JsonSplitWalker:
        '''
        Execute :code:`__floordiv__(key)` of every :class:`JsonWalker` of this
        object and return new :class:`JsonSplitWalker` which combines all of
        the results.

        :param key: a json key (list index or object field name)
        '''
        result: List[JsonWalker] = []
        for walker in self.data:
            new_walker = walker // key
            result.extend(new_walker.data)
        return JsonSplitWalker(result)

    def __add__(self, other: Union[JsonSplitWalker, JsonWalker]) -> JsonSplitWalker:
        '''
        Combine with :class:`JsonWalker` or  another :class:`JsonSplitWalker`
        object.
        '''
        if isinstance(other, JsonWalker):
            data = self.data + [other]
        else:
            data = self.data + other.data
        return JsonSplitWalker(
            [i for i in data if not isinstance(i.data, Exception)])

    def __iter__(self) -> Iterator[JsonWalker]:
        '''
        Yield every :class:`JsonWalker` contained in this object.
        '''
        for i in self.data:
            yield i
