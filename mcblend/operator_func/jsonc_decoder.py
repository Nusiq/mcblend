'''
Adds implementation of JSONDecoder which adds support for C-style comments to
JSON - the JSONCDecoder class.

Please avoid using comments in JSON if you can. They are not part of the
standard for a reason so use it only if you have to.

Source: https://gist.github.com/Nusiq/4d6cc83a6acc8b373b5e56801d273ba3
'''
import json
from json import scanner, JSONDecodeError  # type: ignore
from json.decoder import WHITESPACE, WHITESPACE_STR, scanstring  # type: ignore
import re

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
