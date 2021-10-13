from copy import deepcopy
import collections


def merge(dict1, dict2):
    ''' Return a new dictionary by merging two dictionaries recursively. '''

    result = deepcopy(dict1)

    for key, value in dict2.items():
        if isinstance(value, collections.Mapping):
            result[key] = merge(result.get(key, {}), value)
        elif value is None:
            del result[key]
        else:
            result[key] = deepcopy(dict2[key])

    return result
