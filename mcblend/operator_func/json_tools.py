'''
Utility functions for working with JSON and dictionaries.
'''
from __future__ import annotations
from typing import Iterable, List

def get_vect_json(arr: Iterable, precision: int=3) -> List[float]:
    '''
    Changes the iterable of numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.

    :param arr: an iterable of numbers.
    '''
    result: List[float] = []
    for i in arr:
        i = round(i, precision)
        int_i = int(i)
        if i == int_i:
            result.append(int_i)
        else:
            result.append(i)
    return result
