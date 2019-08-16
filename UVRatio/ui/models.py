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
        self.center = [0, 0]

        self.get_info(dag, component)

        # get ratio
        self.ratio = self.get_ratio()

        # get transform
        if cmds.nodeType(dag.partialPathName()) == "mesh":
            self.transform = cmds.listRelatives(
                dag.partialPathName(), parent=True)[0]
            self.shape = dag.partialPathName()
        else:
            self.transform = dag.partialPathName()
            self.shape = cmds.listRelatives(
                dag.partialPathName(), children=True)[0]

    def get_info(self, dag, component):
        """Gets info needed"""
        mesh_iter = OpenMaya.MItMeshPolygon(dag, component)
        self.count = mesh_iter.count()
        self.uv_indexes = set()

        min_x, min_y = 9999, 9999
        max_x, max_y = -9999, -9999

        while not mesh_iter.isDone():

            self.uv_area += mesh_iter.getUVArea()
            self.world_area += mesh_iter.getArea()

            for v in xrange(mesh_iter.polygonVertexCount()):

                # get index and store it
                self.uv_indexes.add(mesh_iter.getUVIndex(v))

                # check min max value
                x, y = mesh_iter.getUV(v)
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

            mesh_iter.next(1)

        self.center = [((max_x - min_x) / 2.0) + min_x,
                       ((max_y - min_y) / 2.0) + min_y]

    def get_ratio(self):
        try:
            return math.sqrt(self.uv_area / self.world_area)
        except ZeroDivisionError:
            raise RuntimeError(
                "Unable to calculate area because it's zero...")

    def resize(self, new_ratio):
        """
        Resize ratio
        """
        scale_amt = new_ratio / self.ratio

        cmds.polyEditUV(
            ["{0}.map[{1}]".format(self.transform, m)
             for m in self.uv_indexes],
            pivotU=self.center[0],
            pivotV=self.center[1],
            scaleU=scale_amt,
            scaleV=scale_amt)

        self.ratio = new_ratio
