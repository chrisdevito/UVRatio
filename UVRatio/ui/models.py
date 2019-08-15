import math
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

        # get area
        self.uv_area = 0
        self.world_area = 0
        self.get_info(dag, component)

        # get ratio
        self.ratio = self.get_ratio()
        self.transform = dag.partialPathName()

    def get_info(self, dag, component):
        """Gets info needed"""
        mesh_iter = OpenMaya.MItMeshPolygon(dag, component)
        self.count = mesh_iter.count()
        self.uv_indexs = set()

        while not mesh_iter.isDone():
            self.uv_area += mesh_iter.getUVArea()
            self.world_area += mesh_iter.getArea()
            
            vertex_inds = mesh_iter.getVertices()

            for vertex in vertex_inds:
                self.uv_indexs.add(mesh_iter.getUVIndex(vertex))

            mesh_iter.next(1)

        print self.uv_indexs

    def get_ratio(self):
        try:
            return math.sqrt(self.uv_area / self.world_area)
        except ZeroDivisionError:
            raise RuntimeError(
                "Unable to calculate area because it's zero...")

    def resize(self, new_ratio):


        cmds.polyListComponentConversion(fromFace=True, toUV=True)
