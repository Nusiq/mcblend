from unittest.mock import Mock

VERSION = (1, 0, 0)
__version__ = '.'.join([str(x) for x in VERSION])

class Color(Mock): pass
class Euler(Mock): pass
class Matrix(Mock): pass
class Quaternion(Mock): pass
class Vector(Mock): pass
