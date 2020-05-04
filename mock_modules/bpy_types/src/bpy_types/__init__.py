from unittest.mock import Mock

VERSION = (1, 0, 0)
__version__ = '.'.join([str(x) for x in VERSION])


class AddonPreferences(Mock): pass
class Bone(Mock): pass
class Collection(Mock): pass
class CompositorNode(Mock): pass
class Context(Mock): pass
class EditBone(Mock): pass
class Gizmo(Mock): pass
class GizmoGroup(Mock): pass
class Header(Mock): pass
class KeyingSetInfo(Mock): pass
class Library(Mock): pass
class Macro(Mock): pass
class Menu(Mock): pass
class Mesh(Mock): pass
class MeshEdge(Mock): pass
class MeshLoopTriangle(Mock): pass
class MeshPolygon(Mock): pass
class Node(Mock): pass
class NodeInternal(Mock): pass
class NodeSocket(Mock): pass
class NodeSocketInterface(Mock): pass
class NodeTree(Mock): pass
class Object(Mock): pass
class Operator(Mock): pass
class Panel(Mock): pass
class PoseBone(Mock): pass
class PropertyGroup(Mock): pass
class RNAMeta(Mock): pass
class RNAMetaPropGroup(Mock): pass
class RenderEngine(Mock): pass
class ShaderNode(Mock): pass
class Sound(Mock): pass
class StructMetaPropGroup(Mock): pass
class StructRNA(Mock): pass
class Text(Mock): pass
class Texture(Mock): pass
class TextureNode(Mock): pass
class UIList(Mock): pass
class WindowManager(Mock): pass
class WorkSpace(Mock): pass