'''
Extracting data from Molang strings.
'''
from collections import defaultdict
from typing import Optional, Dict, List
from typing import Any, Set
import re

class MolangExpressionResourcesStats:
    '''
    Data class that contains infromation about references to resources detected
    in a molang expression.

    Finds resources that use the "resource_prefix" (e.g texture, geometry
    etc.) in the molang expression. Returns a list of resources. The function
    can use additional argument with list of arrays.

    :param molang: the molang expression.
    :param resource_prefix: the prefix used to identify the type of resource
    :param arrays: MCBLEND_RenderControllerArrayProperties (can't have
        proper type annotation due to blender API abusing annotations for
        different purpose). This is basically a dictionary which uses the
        names of the arrays as keys and has lists of molang expressions as
        values.
    '''
    def __init__(
            self, molang: str, resource_prefix: str,
            arrays: Optional[Any]=None):
        self.resource_prefix = resource_prefix
        self.molang = molang

        self.use_count: Dict[str, int] = defaultdict(int)
        '''
        The number of times a resource is used. It can be either an array or
        direct reference.
        '''

        self.arrays_contents: Dict[str, List[str]] = {}
        '''The contents of arrays mentioned in the use_count'''
        self._load(arrays)

    def _load(self, arrays: Optional[Any]=None):
        '''Loads the data in init.'''
        item_pattern = re.compile(
            f'{self.resource_prefix}\\.\\w+', flags=re.IGNORECASE)
        array_pattern = re.compile(r'array\.\w+', flags=re.IGNORECASE)
        for item_name in item_pattern.findall(self.molang):
            self.use_count[item_name] += 1
        for array_name in array_pattern.findall(self.molang):
            self.use_count[array_name] += 1
            self.arrays_contents[array_name] = []
            if arrays is None or array_name not in arrays.keys():
                continue
            if self.use_count[array_name] > 1:
                continue  # Not the first time we found this array
            self.arrays_contents[array_name] = []
            for array_item in arrays[array_name].items.keys():
                self.arrays_contents[array_name].extend(
                    item_pattern.findall(array_item))
        # Lock use_cout as normal dict
        self.use_count = dict(self.use_count)

    def as_set(self) -> Set[str]:
        '''
        Returns a set of resources used in the expression or referenced
        indirectyl via arrays.
        '''
        result = set()
        for item_name in self.use_count.keys():
            if item_name.startswith("array."):
                result.update(self.arrays_contents[item_name])
            else:
                result.add(item_name)
        print(self.resource_prefix, self.molang)
        print(result, self.use_count, self.arrays_contents)
        return result
