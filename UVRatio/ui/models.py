from maya import cmds
from maya.api import OpenMaya


class Mesh(object):

    def __init__(self):

        active_sel = OpenMaya.MGlobal.getActiveSelectionList()

        if not active_sel:
            raise RuntimeError("Nothing Selected!")

        dag, component = active_sel.getComponent(0)

        if not dag.hasFn(OpenMaya.MFn.kMesh):
            raise RuntimeError("Selected is not a mesh!")

        if not component.isNull():

            if component.hasFn(OpenMaya.MFn.kMeshPolygonComponent):
                pass

            elif component.hasFn(OpenMaya.MFn.kMeshEdgeComponent):
                raise RuntimeError(
                    "Edges not supported! "
                    "Please convert to faces.")

            elif component.hasFn(OpenMaya.MFn.kMeshVertComponent):
                raise RuntimeError(
                    "Vertices/UVs not supported! "
                    "Please convert to faces.")
            else:
                raise RuntimeError("Object is not a mesh!")

        self.ratio = self.get_ratio()

    def get_indices(self):
        return [0, 1, 2]

    def get_ratio(self):
        return 1.0

    @property
    def indices(self):
        return self.indices

    @property
    def ratio(self):
        return self.ratio
