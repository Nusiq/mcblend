'''
Extracting data from Molang strings.
'''
from typing import Optional
from typing import Any, Set
import re

def find_resources(
        molang: str, resource_prefix: str,
        arrays: Optional[Any]=None
    ) -> Set[str]:
    '''
    Finds resources that use the "resource_prefix" (e.g texture, geometry
    etc.) in the molang expression. Returns a list of resources. The function
    can use additional argument with list of arrays.

    :param molang: the molang expression.
    :param resource_prefix: the prefix used to identify the type of resource
    :param arrays: NUSIQ_MCBLEND_RenderControllerArrayProperties (can't have
        proper type annotation due to blender API abusing annotations for
        different purpose). This is basically a dictionary which uses the
        names of the arrays as keys and has lists of molang expressions as
        values.
    '''
    result = set()
    item_pattern = re.compile(f'{resource_prefix}\\.\\w+', flags=re.IGNORECASE)
    array_pattern = re.compile(r'array\.\w+', flags=re.IGNORECASE)

    result.update(item_pattern.findall(molang))
    if arrays is not None:
        for array_name in set(array_pattern.findall(molang)):
            if array_name not in arrays.keys():
                continue
            for array_item in arrays[array_name].items.keys():
                result.update(item_pattern.findall(array_item))
    return result
