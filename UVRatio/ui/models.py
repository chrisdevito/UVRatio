import math
from maya import cmds
from maya.api import OpenMaya


class Mesh(object):

    def __init__(self):

        active_sel = OpenMaya.MGlobal.getActiveSelectionList()

        self.mesh_count = active_sel.length()

        if self.mesh_count == 0:
            raise RuntimeError("Nothing Selected!")

        self.meshes = []
        self.transforms = []
        self.shapes = []

        for x in xrange(self.mesh_count):

            dag, component = active_sel.getComponent(x)

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

            self.meshes.append([dag, component])

            # get transform
            if cmds.nodeType(dag.partialPathName()) == "mesh":
                self.transforms.append(cmds.listRelatives(
                    dag.partialPathName(), parent=True)[0])
                self.shapes.append(dag.partialPathName())
            else:
                self.transforms.append(dag.partialPathName())
                self.shapes.append(cmds.listRelatives(
                    dag.partialPathName(), children=True)[0])

        # init values
        self.uv_area = 0
        self.world_area = 0

        # get info
        self.get_info()

        # get ratio
        self.ratio = self.get_ratio()

    def get_info(self):
        """Gets info needed"""

        min_x, min_y = 9999, 9999
        max_x, max_y = -9999, -9999

        self.counts = []
        self.centers = []
        self.uv_indexes = []

        for dag, component in self.meshes:

            mesh_iter = OpenMaya.MItMeshPolygon(dag, component)
            self.counts.append(mesh_iter.count())
            uv_index = set()

            while not mesh_iter.isDone():

                self.uv_area += mesh_iter.getUVArea()
                self.world_area += mesh_iter.getArea()

                for v in xrange(mesh_iter.polygonVertexCount()):

                    # get index and store it
                    uv_index.add(mesh_iter.getUVIndex(v))

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

            self.centers.append([((max_x - min_x) / 2.0) + min_x,
                                ((max_y - min_y) / 2.0) + min_y])
            self.uv_indexes.append(uv_index)

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

        for i, transform in enumerate(self.transforms):
            cmds.polyEditUV(
                ["{0}.map[{1}]".format(transform, m)
                 for m in self.uv_indexes[i]],
                pivotU=self.centers[i][0],
                pivotV=self.centers[i][1],
                scaleU=scale_amt,
                scaleV=scale_amt)

        self.ratio = new_ratio
