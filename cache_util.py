from functools import wraps
from inspect import signature

__all__ = [
    'cache',
]


def cache(maxsize=128):
    lst = []
    cache_map = {}

    def wrapper(func):
        sig = signature(func)  # 获得参数列表

        @wraps(func)
        def inner(*args, **kwargs):
            bound_values = sig.bind(*args, **kwargs)  # 绑定参数
            # print(bound_values)
            key = bound_values.__str__()
            value = cache_map.get(key)

            if value is not None:
                return value

            if len(lst) >= maxsize:
                oldkey = lst.pop(0)
                if oldkey in cache_map:
                    cache_map.pop(oldkey)

            result = func(*args, **kwargs)
            lst.append(key)
            cache_map[key] = result
            return result

        return inner

    return wrapper
