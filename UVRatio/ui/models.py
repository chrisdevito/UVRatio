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
                    "Vertices not supported! "
                    "Please convert to faces.")

            elif component.hasFn(OpenMaya.MFn.kMeshMapComponent):
                raise RuntimeError(
                    "UVs not supported! "
                    "Please convert to faces.")

            elif component.hasFn(OpenMaya.MFn.kMeshVtxFaceComponent):
                raise RuntimeError(
                    "Vertex Faces not supported! "
                    "Please convert to faces.")

            else:
                raise RuntimeError("Object is not a mesh!")

        self.transform = "what"
        self.ratio = self.get_ratio()
        self.indices = [0, 1, 2]

    def get_ratio(self):
        return 1.0
