VERSION = (1, 0, 0)
__version__ = '.'.join([str(x) for x in VERSION])

# Make submodules visible from here
def __getattr__(attr):
    if attr == 'props':
        import bpy.props as props
        return props
    elif attr == 'types':
        import bpy.types as types
        return types
    else:
        raise AttributeError("module {!r} has no attribute "
                                "{!r}".format(__name__, attr))

def __dir__():
    return list(globals().keys() | {'props', 'types'})