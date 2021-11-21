'''
Utility functions for working with JSON and dictionaries.
'''
from __future__ import annotations
from typing import Iterable, List

def get_vect_json(arr: Iterable) -> List[float]:
    '''
    Changes the iterable of numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.

    :param arr: an iterable of numbers.
    '''
    result = [round(i, 3) for i in arr]
    for i, _ in enumerate(result):
        if result[i] == int(result[i]):
            result[i] = int(result[i])
    return result
