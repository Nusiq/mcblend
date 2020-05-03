VERSION = (1, 0, 0)
__version__ = '.'.join([str(x) for x in VERSION])


# Make submodules visible from here
def __getattr__(attr):
    if attr == 'io_utils':
        import bpy_extras.io_utils as io_utils
        return io_utils
    if attr == 'node_utils':
        import bpy_extras.node_utils as node_utils
        return node_utils
    if attr == 'object_utils':
        import bpy_extras.object_utils as object_utils
        return object_utils
    else:
        raise AttributeError("module {!r} has no attribute "
                                "{!r}".format(__name__, attr))

def __dir__():
    return list(globals().keys() | {'io_utils', 'node_utils', 'object_utils'})