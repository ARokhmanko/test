# coding: utf-8
def object_to_str(obj, ignore_null = False):
    """
    converts any object, including class object, to readable string of fields; works recursively
    isinstance(obj, type) requires py3
    """
    t = type(obj)
    if t in {type}:
        return "{}: {}".format(obj.__class__.__name__, object_to_str(obj.__dict__))
    if t in {list, set, tuple}:
        return str([object_to_str(f) for f in obj if not ignore_null or f])
    if t in {dict}:
        return str({k: object_to_str(v) for k, v in obj.items() if not ignore_null or v})
    return str(obj)
