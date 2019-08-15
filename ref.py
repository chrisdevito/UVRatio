###############################################################################
##
##                    Copyright (c) 2012 Method Studios
##                            All rights reserved.
##
##  This material contains the confidential and proprietary information
##  of Method Studios and may not be disclosed, copied or duplicated in
##  any form, electronic or hardcopy, in whole or in part, without the
##  express prior written consent of Method Studios. This copyright
##  notice does not imply publication.
##
###############################################################################
##
##
##
## $Id$
##
###############################################################################
import os
import math
import re

CHECKER_TYPE_UV_TILE_TEXTURE = 0
CHECKER_TYPE_CHECKER = 1
CHECKER_TYPE_CUSTOM = 2

DIRECTION_HORIZONTAL = 0
DIRECTION_VERTICAL = 1
DIRECTION_BOX = 2

import common.lib.AttrLib as AttrLib
import MayaUtils.NamingHelp as NamingHelp
import common.lib.LookdevLib as LookdevLib
import maya.cmds as cmds
import maya.mel as mel
from Qt_py.Qt import QtCore, QtWidgets, QtGui

######################
# section to convert layers <--> shaders
def shadersToLayers():
    """
    Find all shading groups in the scene and create display layers for each
    containing the assigned objects.  The companion function to this will make
    the conversion the other way.
    """
    cmds.undoInfo(openChunk=True)
    shaders = cmds.ls(type="shadingEngine")
    layer_color_index = 2
    for shader in shaders:
        # The "nodesOnly" flag should use whole objects and ignore face assignments.
        objects = cmds.sets(shader, q=True, nodesOnly=True)
        if not objects: continue
        [cmds.setAttr("%s.overrideEnabled" % (object), 0) for object in objects if
         not cmds.listConnections("%s.overrideEnabled" % (object))]
        objects = cmds.listRelatives(objects, parent=True, fullPath=True)
        material = (cmds.listConnections("%s.surfaceShader" % (shader)) or [None])[0]
        layer = "%s_lyr" % (material)
        if cmds.objExists(layer): cmds.delete(layer)
        cmds.createDisplayLayer(name=layer, empty=True)
        cmds.setAttr("%s.color" % (layer), layer_color_index)
        layer_color_index += 1
        cmds.editDisplayLayerMembers(layer, objects, noRecurse=True)
    cmds.undoInfo(closeChunk=True)


def layersToShaders():
    """
    Find all display layers ending in "_lyr" and assign the corresponding
    material, which should have the same name without that suffix.  The
    companion function to this will make the conversion the other way.
    """
    cmds.undoInfo(openChunk=True)
    old_selection = cmds.ls(sl=True)
    layers = cmds.ls(type="displayLayer") or []
    layers = [layer for layer in layers if layer.endswith("_lyr")]
    for layer in layers:
        objects = cmds.editDisplayLayerMembers(layer, q=True, fullNames=True)
        material = re.sub("_lyr$", "", layer)
        if not cmds.objExists(material):
            print "No material named '%s'.  Cannot convert layer." % (material)
            continue
        cmds.select(objects)
        cmds.hyperShade(assign=material)

    if old_selection:
        cmds.select(old_selection, ne=True)
    else:
        cmds.select(clear=True)
    cmds.undoInfo(closeChunk=True)


def deleteLayersFromShaders():
    cmds.undoInfo(openChunk=True)
    layers = cmds.ls(type="displayLayer")
    layers = [layer for layer in layers if layer.endswith("_lyr")]
    if layers:
        cmds.delete(layers)
    cmds.undoInfo(closeChunk=True)


def udimToUv(udim):
    # TODO: test this.  Not sure if it's right.
    u = (udim - 1001) % 10
    v = (udim - 1001) / 10
    return u, v


#############################
##### Tool button class #####
#############################

class toolButton(QtWidgets.QToolButton):
    def __init__(self, iconFile, parent=None, minSize=48):
        super(toolButton, self).__init__(parent)
        self.setIcon(QtGui.QIcon(iconFile))
        self.setIconSize(QtCore.QSize(32, 32))
        self.setMinimumSize(QtCore.QSize(minSize, minSize))


####################
##### MAIN GUI #####
####################
class m_UVToolsGUI(QtWidgets.QWidget):
    def __init__(self, *args):
        QtWidgets.QWidget.__init__(self, *args)

        ## Dialog Box Settings
        mainVerticalLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainVerticalLayout)
        scrollArea = QtWidgets.QScrollArea()
        widget = QtWidgets.QWidget()
        verticalLayout = QtWidgets.QVBoxLayout()
        widget.setLayout(verticalLayout)
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)

        mainVerticalLayout.addWidget(scrollArea)
        version = os.getenv('REZ_MAYAMODELING_VERSION')
        self.setWindowTitle('UV Tools UI (v%s)' % version)
        self.resize(460, 1200)

        uvOptionsGrpBx = QtWidgets.QGroupBox('UV Editor Options')
        assignGrpBx = QtWidgets.QGroupBox('Assign Checkers')
        offsetGrpBx = QtWidgets.QGroupBox('Set UV Tile')
        udimGrpBx = QtWidgets.QGroupBox('Set UDIM')
        directionGrpBx = QtWidgets.QGroupBox('Offset UV Position')
        mirrorGrpBx = QtWidgets.QGroupBox('Mirror Selected Shell')
        alignGrpBx = QtWidgets.QGroupBox('Align Shell to UV')
        layoutGrpBx = QtWidgets.QGroupBox('Lay Out UVs for Selected')
        shadersToLayersGrpBx = QtWidgets.QGroupBox('Layers to/from Shaders')
        uvWorldSpaceRatioGrpBx = QtWidgets.QGroupBox('UV World Space')
        uvIntersectionCheckGrpBx = QtWidgets.QGroupBox('Check UV Intersection')
        exportObjByUDIMGrpBx = QtWidgets.QGroupBox('Export OBJ by UDIM')
        resetGrpBx = QtWidgets.QGroupBox('Reset')
        toggleShadersGrpBx = QtWidgets.QGroupBox('Toggle Shaders')        
        packageRoot = os.getenv('REZ_MAYAMODELING_ROOT')
        iconPath = os.path.join(packageRoot, 'icons')

        ## assignGrpBx widgets
        uvOptionsVertLayout = QtWidgets.QVBoxLayout(uvOptionsGrpBx)
        self.component_spacing_checkbox = QtWidgets.QCheckBox("Retain component spacing")
        self.component_spacing_checkbox.setChecked(self.getUvRetainComponentSpacingValue())
        self.component_spacing_checkbox.clicked.connect(self.uvRetainComponentSpacingCallback)
        uvOptionsVertLayout.addWidget(self.component_spacing_checkbox)

        ## assignGrpBx widgets
        verAssignLayout = QtWidgets.QVBoxLayout(assignGrpBx)
        checkerHorLayout = QtWidgets.QHBoxLayout()
        self.type1ToolButton = toolButton(os.path.join(iconPath, 'checkerIcon1.png'))
        self.type2ToolButton = toolButton(os.path.join(iconPath, 'checkerIcon2.png'))
        self.type3ToolButton = toolButton(os.path.join(iconPath, 'checkerIcon3.png'))
        self.copyType1ToolButton = toolButton(os.path.join(iconPath, 'checkerIcon1.png'))
        

        checkerHorLayout.addWidget(self.type1ToolButton)
        checkerHorLayout.addWidget(self.type2ToolButton)
        checkerHorLayout.addWidget(self.type3ToolButton)

        verAssignLayout.addLayout(checkerHorLayout)

        hor2Layout = QtWidgets.QHBoxLayout()
        repeatLabel = QtWidgets.QLabel('Repeat:')
        uLabel1 = QtWidgets.QLabel('U')
        self.uSpinBox1 = QtWidgets.QDoubleSpinBox()
        self.uSpinBox1.setRange(0.0, 1000.0)
        self.uSpinBox1.setValue(1.0)
        self.uSpinBox1.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)

        vLabel1 = QtWidgets.QLabel('V')
        self.vSpinBox1 = QtWidgets.QDoubleSpinBox()
        self.vSpinBox1.setRange(0.0, 1000.0)
        self.vSpinBox1.setValue(1.0)
        self.vSpinBox1.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
        self.repeatButton = QtWidgets.QPushButton('Apply Repeats')
        self.repeatButton.setMaximumHeight(20)

        hor2Layout.addWidget(repeatLabel)
        hor2Layout.addWidget(uLabel1)
        hor2Layout.addWidget(self.uSpinBox1)
        hor2Layout.addWidget(vLabel1)
        hor2Layout.addWidget(self.vSpinBox1)
        hor2Layout.addWidget(self.repeatButton)

        verAssignLayout.addLayout(hor2Layout)

        ## offsetGrpBx Widgets
        verUvTileLayout = QtWidgets.QVBoxLayout(offsetGrpBx)

        horUvTileLayout = QtWidgets.QHBoxLayout()
        verUvTileLayout.addLayout(horUvTileLayout)

        uLabel2 = QtWidgets.QLabel('U')
        self.uSpinBox2 = QtWidgets.QSpinBox()
        self.uSpinBox2.setRange(0, 99)
        self.uSpinBox2.setValue(1)
        self.uSpinBox2.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)

        vLabel2 = QtWidgets.QLabel('V')
        self.vSpinBox2 = QtWidgets.QSpinBox()
        self.vSpinBox2.setRange(0, 99)
        self.vSpinBox2.setValue(1)
        self.vSpinBox2.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)

        self.offsetButton = QtWidgets.QPushButton('Set UV Tile')
        self.offsetButton.setMaximumHeight(20)

        horUvTileLayout.addWidget(uLabel2)
        horUvTileLayout.addWidget(self.uSpinBox2)
        horUvTileLayout.addWidget(vLabel2)
        horUvTileLayout.addWidget(self.vSpinBox2)
        horUvTileLayout.addSpacing(40)
        horUvTileLayout.addWidget(self.offsetButton)

        ## udimGrpBx Widgets
        verUdimLayout = QtWidgets.QVBoxLayout(udimGrpBx)

        horUdimLayout = QtWidgets.QHBoxLayout()
        verUdimLayout.addLayout(horUdimLayout)

        udimLabel = QtWidgets.QLabel('UDIM')
        self.udimSpinBox = QtWidgets.QSpinBox()
        self.udimSpinBox.setRange(1001, 1999)
        self.udimSpinBox.setValue(1001)

        self.udimButton = QtWidgets.QPushButton('Set UDIM')
        self.udimButton.setMaximumHeight(20)

        horUdimLayout.addWidget(udimLabel)
        horUdimLayout.addWidget(self.udimSpinBox)
        horUdimLayout.addSpacing(40)
        horUdimLayout.addWidget(self.udimButton)

        ## directionGrpBx Widgets
        direction_vert_layout = QtWidgets.QVBoxLayout(directionGrpBx)
        direction_grid_layout = QtWidgets.QGridLayout()
        direction_grid_layout.setAlignment(QtCore.Qt.AlignCenter)
        direction_grid_layout.setColumnStretch(0, 0)

        self.left_up_button = toolButton(os.path.join(iconPath, 'left_up_arrow.xpm'),
                                         minSize=32)
        self.up_button = toolButton(os.path.join(iconPath, 'up_arrow.xpm'),
                                    minSize=32)
        self.right_up_button = toolButton(
            os.path.join(iconPath, 'right_up_arrow.xpm'), minSize=32)
        self.left_button = toolButton(os.path.join(iconPath, 'left_arrow.xpm'),
                                      minSize=32)
        self.right_button = toolButton(os.path.join(iconPath, 'right_arrow.xpm'),
                                       minSize=32)
        self.left_down_button = toolButton(
            os.path.join(iconPath, 'left_down_arrow.xpm'), minSize=32)
        self.down_button = toolButton(os.path.join(iconPath, 'down_arrow.xpm'),
                                      minSize=32)
        self.right_down_button = toolButton(
            os.path.join(iconPath, 'right_down_arrow.xpm'), minSize=32)

        self.left_up_button.clicked.connect(lambda u=-1, v=1: self.offsetUVCallback(u, v))
        self.up_button.clicked.connect(lambda u=0, v=1: self.offsetUVCallback(u, v))
        self.right_up_button.clicked.connect(lambda u=1, v=1: self.offsetUVCallback(u, v))
        self.left_button.clicked.connect(lambda u=-1, v=0: self.offsetUVCallback(u, v))
        self.right_button.clicked.connect(lambda u=1, v=0: self.offsetUVCallback(u, v))
        self.left_down_button.clicked.connect(lambda u=-1, v=-1: self.offsetUVCallback(u, v))
        self.down_button.clicked.connect(lambda u=0, v=-1: self.offsetUVCallback(u, v))
        self.right_down_button.clicked.connect(lambda u=1, v=-1: self.offsetUVCallback(u, v))


        direction_grid_layout.addWidget(self.left_up_button, 0, 0)
        direction_grid_layout.addWidget(self.up_button, 0, 1)
        direction_grid_layout.addWidget(self.right_up_button, 0, 2)
        direction_grid_layout.addWidget(self.left_button, 1, 0)
        direction_grid_layout.addWidget(self.right_button, 1, 2)
        direction_grid_layout.addWidget(self.left_down_button, 2, 0)
        direction_grid_layout.addWidget(self.down_button, 2, 1)
        direction_grid_layout.addWidget(self.right_down_button, 2, 2)

        self.wrap_around_checkbox = QtWidgets.QCheckBox("Wrap around U value")
        self.wrap_around_checkbox.setChecked(False)
        direction_vert_layout.addLayout(direction_grid_layout)
        direction_vert_layout.addWidget(self.wrap_around_checkbox)

        ## mirrorGrpBx Widgets
        mirror_vert_layout = QtWidgets.QVBoxLayout(mirrorGrpBx)
        mirror_button_layout = QtWidgets.QHBoxLayout()

        self.mirror_u_button = QtWidgets.QPushButton("Mirror Horizontally")
        self.mirror_u_button.setMaximumHeight(20)
        self.mirror_v_button = QtWidgets.QPushButton("Mirror Vertically")
        self.mirror_v_button.setMaximumHeight(20)

        self.mirror_u_button.clicked.connect(lambda u=-1, v=1: self.mirrorUvCallback(u, v))
        self.mirror_v_button.clicked.connect(lambda u=1, v=-1: self.mirrorUvCallback(u, v))

        mirror_button_layout.addWidget(self.mirror_u_button)
        mirror_button_layout.addWidget(self.mirror_v_button)
        mirror_vert_layout.addLayout(mirror_button_layout)

        ## alignGrpBx Widgets
        align_vert_layout = QtWidgets.QVBoxLayout(alignGrpBx)
        align_grid_layout = QtWidgets.QGridLayout()
        align_grid_layout.setAlignment(QtCore.Qt.AlignCenter)
        align_grid_layout.setColumnStretch(0, 0)

        self.align_left_up_button = toolButton(
            os.path.join(iconPath, 'line_arrow_left_up.xpm'), minSize=32)
        self.align_up_button = toolButton(os.path.join(iconPath, 'line_arrow_up.xpm'),
                                          minSize=32)
        self.align_right_up_button = toolButton(
            os.path.join(iconPath, 'line_arrow_right_up.xpm'), minSize=32)
        self.align_left_button = toolButton(
            os.path.join(iconPath, 'line_arrow_left.xpm'), minSize=32)
        self.align_right_button = toolButton(
            os.path.join(iconPath, 'line_arrow_right.xpm'), minSize=32)
        self.align_left_down_button = toolButton(
            os.path.join(iconPath, 'line_arrow_left_down.xpm'), minSize=32)
        self.align_down_button = toolButton(
            os.path.join(iconPath, 'line_arrow_down.xpm'), minSize=32)
        self.align_right_down_button = toolButton(
            os.path.join(iconPath, 'line_arrow_right_down.xpm'), minSize=32)

        self.align_left_up_button.clicked.connect(lambda angle=135: self.alignUvCallback(angle))
        self.align_up_button.clicked.connect(lambda angle=90: self.alignUvCallback(angle))
        self.align_right_up_button.clicked.connect(lambda angle=45: self.alignUvCallback(angle))
        self.align_left_button.clicked.connect(lambda angle=180: self.alignUvCallback(angle))
        self.align_right_button.clicked.connect(lambda angle=0: self.alignUvCallback(angle))
        self.align_left_down_button.clicked.connect(lambda angle=225: self.alignUvCallback(angle))
        self.align_down_button.clicked.connect(lambda angle=270: self.alignUvCallback(angle))
        self.align_right_down_button.clicked.connect(lambda angle=315: self.alignUvCallback(angle))


        align_grid_layout.addWidget(self.align_left_button, 0, 0)
        align_grid_layout.addWidget(self.align_right_button, 1, 0)
        align_grid_layout.addWidget(self.align_up_button, 0, 1)
        align_grid_layout.addWidget(self.align_down_button, 1, 1)
        align_grid_layout.addWidget(self.align_left_up_button, 0, 2)
        align_grid_layout.addWidget(self.align_right_up_button, 1, 2)
        align_grid_layout.addWidget(self.align_left_down_button, 0, 3)
        align_grid_layout.addWidget(self.align_right_down_button, 1, 3)


        align_vert_layout.addLayout(align_grid_layout)

        # layout group box
        layoutVerLayout = QtWidgets.QVBoxLayout(layoutGrpBx)
        layoutButtonLayout = QtWidgets.QHBoxLayout()
        self.layOutHor = QtWidgets.QPushButton("Horizonally")
        self.layOutHor.setMaximumHeight(20)
        self.layOutVer = QtWidgets.QPushButton("Vertically")
        self.layOutVer.setMaximumHeight(20)
        self.layOutBox = QtWidgets.QPushButton("Box")
        self.layOutBox.setMaximumHeight(20)
        self.spacingLayout = QtWidgets.QHBoxLayout()
        self.spacingLabel = QtWidgets.QLabel("Spacing")
        self.spacingLabel.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.spacingSpinBox = QtWidgets.QDoubleSpinBox()
        self.spacingSpinBox.setRange(0.001, 1000.0)
        self.spacingSpinBox.setDecimals(3)
        self.spacingSpinBox.setValue(0.0)
        self.spacingSpinBox.setSingleStep(0.1)
        self.spacingSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
        layoutButtonLayout.addWidget(self.layOutHor)
        layoutButtonLayout.addWidget(self.layOutVer)
        layoutButtonLayout.addWidget(self.layOutBox)
        layoutVerLayout.addLayout(layoutButtonLayout)
        self.spacingLayout.addWidget(self.spacingLabel)
        self.spacingLayout.addWidget(self.spacingSpinBox)
        layoutVerLayout.addLayout(self.spacingLayout)

        self.layOutHor.clicked.connect(lambda direction=DIRECTION_HORIZONTAL: self.layOutPieces(direction))
        self.layOutVer.clicked.connect(lambda direction=DIRECTION_VERTICAL: self.layOutPieces(direction))
        self.layOutBox.clicked.connect(lambda direction=DIRECTION_BOX: self.layOutPieces(direction))

        # shaders to layers
        shadersToLayersLayout = QtWidgets.QVBoxLayout(shadersToLayersGrpBx)
        self.shadersToLayersButton = QtWidgets.QPushButton("Shaders To Layers")
        self.layersToShadersButton = QtWidgets.QPushButton("Layers To Shaders")
        self.removeLayersButton = QtWidgets.QPushButton("Remove Shader Layers")
        shadersToLayersLayout.addWidget(self.shadersToLayersButton)
        shadersToLayersLayout.addWidget(self.layersToShadersButton)
        shadersToLayersLayout.addWidget(self.removeLayersButton)

        self.shadersToLayersButton.clicked.connect(shadersToLayers)
        self.layersToShadersButton.clicked.connect(layersToShaders)
        self.removeLayersButton.clicked.connect(deleteLayersFromShaders)


        # uv world space
        uvWorldSpaceLayout = QtWidgets.QVBoxLayout(uvWorldSpaceRatioGrpBx)
        uvWorldSpaceEditLayout = QtWidgets.QHBoxLayout()
        uvWorldSpaceRatioLabel = QtWidgets.QLabel("World Space Ratio")
        uvWorldSpaceRatioLineEdit = QtWidgets.QLineEdit()

        self.uvWorldSpaceRatioSpinBox = QtWidgets.QDoubleSpinBox()
        tooltip = "<html>This is the UV to world space ratio.  If the value is set to 1.0, then 1 world space unit should translate to 1 unit in UV space.  If the ratio is 2, that means 1 world space unit becomes 2 units in UV space."
        self.uvWorldSpaceRatioSpinBox.setToolTip(tooltip)
        self.uvWorldSpaceRatioSpinBox.setRange(0.001, 1000.0)
        self.uvWorldSpaceRatioSpinBox.setDecimals(6)
        self.uvWorldSpaceRatioSpinBox.setValue(1.0)
        self.uvWorldSpaceRatioSpinBox.setSingleStep(0.1)
        self.uvWorldSpaceRatioSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)

        setUvWorldSpaceButton = QtWidgets.QPushButton("Set UV World Space")
        setUvWorldSpaceButton.setMaximumHeight(20)
        setUvRatioToSelectionButton = QtWidgets.QPushButton("Update Ratio Based on Selection")
        setUvRatioToSelectionButton.setMaximumHeight(20)
        tooltip = "<html>This button will update the number for the world space UV ratio to match that of your current selection.  This makes it easy to copy the UV ratio from one object to another."
        setUvRatioToSelectionButton.setToolTip(tooltip)
        uvWorldSpaceEditLayout.addWidget(uvWorldSpaceRatioLabel)
        uvWorldSpaceEditLayout.addWidget(self.uvWorldSpaceRatioSpinBox)
        uvWorldSpaceEditLayout.addWidget(setUvRatioToSelectionButton)
        uvWorldSpaceLayout.addLayout(uvWorldSpaceEditLayout)
        uvWorldSpaceLayout.addWidget(setUvWorldSpaceButton)

        setUvRatioToSelectionButton.clicked.connect(self.setUvRatioToSelection)
        setUvWorldSpaceButton.clicked.connect(self.setUvWorldSpaceRatio)

        # uv intersection check
        uvIntersectionCheckLayout = QtWidgets.QVBoxLayout(uvIntersectionCheckGrpBx)
        uvIntersectionCheckHLayout = QtWidgets.QHBoxLayout()
        self.threadedChkBx = QtWidgets.QCheckBox('Threaded')
        self.threadedChkBx.setChecked(QtCore.Qt.Unchecked)
        tooltip = "<html>MultiThreaded version of the plugin (Is unstable)"
        self.threadedChkBx.setToolTip(tooltip)
        self.borderOnlyUVsChkBx = QtWidgets.QCheckBox('Border UVs Only')
        self.borderOnlyUVsChkBx.setChecked(QtCore.Qt.Checked)
        self.findAllChkBx = QtWidgets.QCheckBox('Find All')
        self.toleranceDSpnBx = QtWidgets.QDoubleSpinBox()
        self.toleranceDSpnBx.setRange(0.0, 1.0)
        self.toleranceDSpnBx.setValue(0.05)
        tooltip = "<html>Higher tolerance will account for more edges being evaluated but will increase evalution time"
        self.toleranceDSpnBx.setToolTip(tooltip)
        toleranceLbl = QtWidgets.QLabel('Tolerance')
        uvIntersectionCheckHLayout.addWidget(self.borderOnlyUVsChkBx)
        uvIntersectionCheckHLayout.addWidget(self.findAllChkBx)
        uvIntersectionCheckHLayout.addWidget(self.toleranceDSpnBx)
        uvIntersectionCheckHLayout.addWidget(toleranceLbl)
        self.uvInterSectionBtn = QtWidgets.QPushButton('Check UV Intersections')

        uvIntersectionCheckLayout.addLayout(uvIntersectionCheckHLayout)
        uvIntersectionCheckLayout.addWidget(self.uvInterSectionBtn)

        self.uvInterSectionBtn.clicked.connect(self.uvInterSectionBtnCB)

        # export OBJ by UDIM
        exportObjByUDIMLayout = QtWidgets.QVBoxLayout(exportObjByUDIMGrpBx)
        exportObjByUDIMHLayout1 = QtWidgets.QHBoxLayout()
        pathLbl = QtWidgets.QLabel('Path:')
        self.pathLineEdt = QtWidgets.QLineEdit()
        self.pathBrowseBtn = QtWidgets.QPushButton('Browse')
        self.pathBrowseBtn.setMaximumHeight(20)
        exportObjByUDIMHLayout1.addWidget(pathLbl)
        exportObjByUDIMHLayout1.addWidget(self.pathLineEdt)
        exportObjByUDIMHLayout1.addWidget(self.pathBrowseBtn)
        exportObjByUDIMHLayout2 = QtWidgets.QHBoxLayout()
        self.moveTOUDIM = QtWidgets.QCheckBox('Move to Set UDIM')
        self.moveTOUDIM.setChecked(QtCore.Qt.Checked)
        self.exportBtn = QtWidgets.QPushButton('Export')
        self.exportBtn.setMaximumHeight(20)
        exportObjByUDIMHLayout2.addWidget(self.moveTOUDIM)
        exportObjByUDIMHLayout2.addWidget(self.exportBtn)
        exportObjByUDIMLayout.addLayout(exportObjByUDIMHLayout1)
        exportObjByUDIMLayout.addLayout(exportObjByUDIMHLayout2)

        self.pathBrowseBtn.clicked.connect(self.pathBrowseBtnCallBack)
        self.exportBtn.clicked.connect(self.exportBtnCallBack)

        # reset group box
        hor5Layout = QtWidgets.QHBoxLayout(resetGrpBx)
        self.resetShadersButton = QtWidgets.QPushButton('Reset Shaders')
        self.resetShadersButton.setMaximumHeight(20)
        self.resetOffsetsButton = QtWidgets.QPushButton('Reset Offsets')
        self.resetOffsetsButton.setMaximumHeight(20)

        hor5Layout.addWidget(self.resetShadersButton)
        hor5Layout.addWidget(self.resetOffsetsButton)
        
        # toggle Shaders group box
        hor6Layout = QtWidgets.QHBoxLayout(toggleShadersGrpBx)
        self.createLayersButton = QtWidgets.QPushButton('Create Mtl Layers')
        self.createLayersButton.setMaximumHeight(20)
        self.reassignMtlsButton = QtWidgets.QPushButton('Reassign Mtls')
        self.reassignMtlsButton.setMaximumHeight(20)
        self.recreateFromXmlButton = QtWidgets.QPushButton('Recreate Mtls from Xml')
        self.recreateFromXmlButton.setMaximumHeight(20)

        hor6Layout.addWidget(self.createLayersButton)
        hor6Layout.addWidget(self.reassignMtlsButton)
        hor6Layout.addWidget(self.recreateFromXmlButton)
        hor6Layout.addWidget(self.copyType1ToolButton)

        ## add to main layout
        verticalLayout.addWidget(uvOptionsGrpBx)
        verticalLayout.addWidget(assignGrpBx)
        verticalLayout.addWidget(offsetGrpBx)
        verticalLayout.addWidget(udimGrpBx)
        verticalLayout.addWidget(directionGrpBx)
        verticalLayout.addWidget(mirrorGrpBx)
        verticalLayout.addWidget(alignGrpBx)
        verticalLayout.addWidget(layoutGrpBx)
        verticalLayout.addWidget(shadersToLayersGrpBx)
        verticalLayout.addWidget(uvWorldSpaceRatioGrpBx)
        verticalLayout.addWidget(uvIntersectionCheckGrpBx)
        verticalLayout.addWidget(exportObjByUDIMGrpBx)
        verticalLayout.addWidget(resetGrpBx)
        verticalLayout.addWidget(toggleShadersGrpBx)

        self.type1ToolButton.clicked.connect(lambda checker_type=CHECKER_TYPE_UV_TILE_TEXTURE: self.assignTypeCheckers(checker_type))
        self.copyType1ToolButton.clicked.connect(lambda checker_type=CHECKER_TYPE_UV_TILE_TEXTURE: self.assignTypeCheckers(checker_type))        
        self.type2ToolButton.clicked.connect(lambda checker_type=CHECKER_TYPE_CHECKER: self.assignTypeCheckers(checker_type))
        self.type3ToolButton.clicked.connect(lambda checker_type=CHECKER_TYPE_CUSTOM: self.assignTypeCheckers(checker_type))

        self.repeatButton.clicked.connect(self.applyRepeats)
        self.offsetButton.clicked.connect(self.setUVPositionCallback)
        self.udimButton.clicked.connect(self.setUdimPositionCallback)
        self.resetShadersButton.clicked.connect(self.clearShaders)
        self.resetOffsetsButton.clicked.connect(self.resetOffsets)
        self.createLayersButton.clicked.connect(self.createMtlLayers)        
        self.reassignMtlsButton.clicked.connect(self.reassignMtls)
        self.recreateFromXmlButton.clicked.connect(self.recreateMtlsFromXml)
        
    def recreateMtlsFromXml(self):
        """
        Function to recreate material assignments from the published xml file
        """
        namingHelp = NamingHelp.getNamingHelper()
        try:
            modelTopNode = cmds.ls(sl=True)[0]
        except:
            modelTopNode = "None"
        try:
            show = cmds.getAttr('%s.show'%modelTopNode)
            seq = cmds.getAttr('%s.seq'%modelTopNode)
            shot = cmds.getAttr('%s.shot'%modelTopNode)
            product = cmds.getAttr('%s.product'%modelTopNode)
            task = cmds.getAttr('%s.task'%modelTopNode)
            lod = cmds.getAttr('%s.rep'%modelTopNode)
            version = cmds.getAttr('%s.version'%modelTopNode)
        except:
            print "Please select the top node of the model"
            cmds.confirmDialog( title='Warning', message='Please select the model top node first\nthen try again.', button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )
            return
        mtlXml = namingHelp.getAssetMetaFilePath(show, seq, shot, product, task, lod, version, 'xml')
        if os.path.exists(mtlXml):
            LookdevLib.recreateMtlFromXml(mtlXml)            
            #Try to delete any layers that might already exist based on these material names
            sceneMtlsList = cmds.ls(mat=True)
            for mtl in sceneMtlsList:
                layerName = '%s_%s' % (mtl, 'layer')
                if cmds.objExists(layerName) and re.search("_mtl", mtl):
                    cmds.delete(layerName)
            #recreateMtlFromXml may have corrected the name of the uvMtl and its shading group.  Set the name back to what it was"
            uvMtlShadingGrp = "uvTools_checker1"
            uvMtl = "uvTools_checker1_mtl"
            if cmds.objExists(uvMtl):
                originalMtlName = "uvTools_checker1"
                originalSGName = "uvTools_checker1SG"
                cmds.rename(uvMtlShadingGrp, originalSGName)
                cmds.rename(uvMtl, originalMtlName)
        else:
            cmds.confirmDialog( title='Warning', message='Material Xml not found.\nSkipping....', button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )
        cmds.select(cl=True)            

    def createMtlLayers(self):
        """
        Function that reads the materials in the scene, creates display layers matching the material names
        and assign objects to the layers corresponding to the objects attached to the materials
        """      
        sceneMtlsList = cmds.ls(mat=True)
        mtlObjectDict = {}
        for mtl in sceneMtlsList:
            cmds.hyperShade(objects=mtl)
            currentObjects = cmds.ls(sl=True)
            mtlObjectDict[mtl] = currentObjects
    
        for mtl in mtlObjectDict.keys():
            if re.search("_mtl", mtl) or mtl == "lambert1":
                layerName = '%s_%s' % (mtl,"layer")
                if mtl == "lambert1":
                    layerName = "UNASSIGNED"
                if len(mtlObjectDict[mtl]):
                    if not cmds.objExists(layerName):
                        cmds.createDisplayLayer(name=layerName, number=1, empty=True)
                        #cmds.createDisplayLayer(name=layerName, empty=True)                        
                    cmds.select(cl=True)
                    #We need the shape nodes, because when you select an object to put into a display layer manually in the interface, it is the shape node
                    #that gets the connection
                    objectsToSelect = []
                    for obj in mtlObjectDict[mtl]:
                        cmds.select(cl=True)
                        cmds.select(obj)
                        relatives = cmds.listRelatives(s=True)
                        if relatives is not None:
                            objectsToSelect += relatives
                        else:
                            objectsToSelect += [obj]
                    cmds.select(objectsToSelect)
                    if len(mtlObjectDict[mtl]):
                        cmds.select(cl=True)
                        #cmds.select(mtlObjectDict[mtl])
                        objsToSelect = ""
                        for object in mtlObjectDict[mtl]:
                            objsToSelect += object + " "
                        cmd = "select -r %s" % (objsToSelect)
                        mel.eval(cmd)
                        #cmd = "editDisplayLayerMembers -noRecurse %s `ls -selection`" % (layerName)
                        cmd = "layerEditorAddObjects %s;" % (layerName)
                        mel.eval(cmd)
                        #editDisplayLayerMembers -noRecurse test2 `ls -selection`;
                        #cmds.editDisplayLayerMembers(layerName, mtlObjectDict[mtl], noRecurse=False)
        cmds.select(cl=True)

    def reassignMtls(self):
        """
        Function that looks for display layers with names corresponding to materials in the scene.  Objects assigned to the layer
        have the correspondingly named material assigned to them.  The layer are then deleted
        """
        sceneMtlsList = cmds.ls(mat=True)
        layers = []
        for mtl in sceneMtlsList:
            layerName = '%s_%s' % (mtl, 'layer')
            if mtl == "lambert1":
                layerName = "UNASSIGNED"
            layers.append(layerName)
            if cmds.objExists(layerName) and re.search("_mtl", mtl):
                cmd = 'layerEditorSelectObjects %s' % layerName
                mel.eval(cmd)
                selectedObjects = cmds.ls(sl=True)
                objectsToAssign = []
                for object in selectedObjects:
                    #If an object is assigned to a new layer, maya assigns the old layer to the transform node.  Make sure we are dealing with
                    # the shape nodes
                    cmds.select(cl=True)
                    cmds.select(object)
                    relatives = cmds.listRelatives(s=True)
                    if relatives is not None:
                        shapeNode = relatives[0]
                        cmds.select(cl=True)
                        cmds.select(shapeNode)                        
                        displayLayer = cmds.listConnections(s=True, t="displayLayer")
                        if displayLayer is not None:
                            displayLayer = displayLayer[0]
                            if displayLayer == layerName:
                                objectsToAssign.append(shapeNode)
                            else:
                                objectsToAssign.append(object)
                    else:
                        parent = cmds.listRelatives(p=True)
                        if parent is not None:
                            parent = parent[0]
                            cmds.select(parent,r=True)
                            displayLayer = cmds.listConnections(s=True, t="displayLayer")
                            if displayLayer is not None:
                                displayLayer = displayLayer[0]
                                if displayLayer == layerName:
                                    objectsToAssign.append(parent)
                            else:
                                objectsToAssign.append(object)
                        else:
                            objectsToAssign.append(object)
                cmds.select(cl=True)
                if len(objectsToAssign):
                    cmds.select(objectsToAssign)
                    #Find the shading group
                    sgList = cmds.listConnections('%s.outColor' % mtl) or []
                    sg = sgList[0]
                    #Assign
                    if len(sgList):
                        cmds.sets(e=True, forceElement=sg)
        for layer in layers:
            #Delete the layers
            if cmds.objExists(layer):
                cmds.delete(layer)
        cmds.select(cl=True)                

    def getUvArea(self, object):
        """
        Pilfered this function from a forum post on CG society, specifically this --
        http://forums.cgsociety.org/archive/index.php/t-884105.html
        """
        import maya.OpenMaya as om
        mayaAppVer = os.getenv('METHOD_MAYA_VERSION_')
        sList = om.MSelectionList()
        sList.add(object) # hard-coded object name here
        sIter = om.MItSelectionList(sList)
        dagp = om.MDagPath()
        mobj = om.MObject()
        sIter.getDagPath(dagp, mobj)
        pIter = om.MItMeshPolygon(dagp)
        areaParam = om.MScriptUtil()
        areaParam.createFromDouble(0.0)
        areaPtr = areaParam.asDoublePtr()
        totalArea = 0.0
        while not pIter.isDone():
            if mayaAppVer == '2011':
                pIter.getUVArea(areaPtr)
                area = om.MScriptUtil(areaPtr).asDouble()
            else:
                pIter.getUVArea(areaPtr)
                area = om.MScriptUtil.getDouble(areaPtr)
            totalArea += area
            pIter.next()
        return totalArea

    def get3dArea(self, object):
        cmds.select(object)
        return cmds.polyEvaluate(worldArea=True)

    def jogUVs(self, objects):
        """
        MEGA HACKY.
        There are cases where the UV area call doesn't work accurately
        and it seems like we need to jog it by kicking the UVs.  Adding a UV
        merge and then deleting it immediately after seems to do it.
        """
        nodes = [cmds.polyMergeUV(object, d=0, ch=1)[0] for object in objects]
        cmds.delete(nodes)
        cmds.delete(objects, constructionHistory=True)

    def setUvRatioToSelection(self):
        """
        Set the UV ratio float to equal that of the current selection.
        """
        cmds.undoInfo(openChunk=True)
        old_selection = cmds.ls(sl=True, noIntermediate=True)
        if not old_selection: return
        ratio = math.pow(self.uvWorldSpaceRatioSpinBox.value(), 2)
        objects = cmds.polyListComponentConversion(old_selection)
        objects = list(set(cmds.ls(objects, dag=True, type="mesh", noIntermediate=True)))
        self.jogUVs(objects)
        world_space = 0
        uv_space = 0
        for object in objects:
            world_space += self.get3dArea(object)
            uv_space += self.getUvArea(object)
        ratio = math.sqrt(uv_space / world_space)
        self.uvWorldSpaceRatioSpinBox.setValue(ratio)
        if old_selection:
            cmds.select(old_selection, ne=True)

    def setUvWorldSpaceRatio(self):
        """
        Based on the world space ratio entered in the interface, update all
        selected objects to use that ratio and scale them around their UV
        center pivot.
        """
        cmds.undoInfo(openChunk=True)
        old_selection = cmds.ls(sl=True, noIntermediate=True)
        if not old_selection: return
        ratio = math.pow(self.uvWorldSpaceRatioSpinBox.value(), 2)
        objects = cmds.polyListComponentConversion(old_selection)
        objects = list(set(cmds.ls(objects, dag=True, type="mesh", noIntermediate=True)))
        self.jogUVs(objects)
        for object in objects:
            world_space = self.get3dArea(object)
            uv_space = self.getUvArea(object)
            uv_scale = math.sqrt(ratio * world_space / uv_space)
            cmds.select(object)
            ((umin, umax), (vmin, vmax)) = cmds.polyEvaluate(object, b2=True)
            u_pivot = (umin + umax) * 0.5
            v_pivot = (vmin + vmax) * 0.5
            uvs = cmds.polyListComponentConversion(object, toUV=True)
            if not uvs:
                print "object '%s' has no UVs." % (object)
                continue
            cmds.select(uvs)
            #cmds.select(object)
            cmds.polyEditUV(pivotU=u_pivot, pivotV=v_pivot, scaleU=uv_scale, scaleV=uv_scale)
        if old_selection:
            cmds.select(old_selection, ne=True)
        cmds.undoInfo(closeChunk=True)

    def getSelectionAndUVs(self, mode):
        """
            DESCRIPTION
                Procedure to get u,v values from the UI and selection
                list from maya
            ARGS
            ----------------------------------------------------------------
            mode = bool 0 : repeat uv values, 1 : offset uv values
            ----------------------------------------------------------------
            RETURNS
                sel list
                u float
                v float

        """
        sel = cmds.ls(sl=True)
        if not mode:
            u = self.uSpinBox1.value()
            v = self.vSpinBox1.value()
        else:
            u = self.uSpinBox2.value()
            v = self.vSpinBox2.value()

        return sel, u, v

    def getSelectionAndUdim(self):
        """ return selection and udim """
        sel = cmds.ls(sl=True)
        value = self.udimSpinBox.value()
        return sel, value

    def assignTypeCheckers(self, checker_type=CHECKER_TYPE_UV_TILE_TEXTURE):
        sel, u, v = self.getSelectionAndUVs(0)
        if not sel:
            warn = 'Nothing selected to assign'
            QtWidgets.QMessageBox.warning(self, 'Error', warn)
            return

        if checker_type == CHECKER_TYPE_UV_TILE_TEXTURE:
            checker_name = "uvTools_checker1"
            packageRoot = os.getenv('REZ_MAYAMODELING_ROOT')
            checker_tex_path = os.path.join(packageRoot, 'images', 'uv.tif')
        elif checker_type == CHECKER_TYPE_CHECKER:
            checker_name = "uvTools_checker2"
            checker_tex_path = ""
        elif checker_type == CHECKER_TYPE_CUSTOM:
            show = os.getenv('JOB_')
            seq = os.getenv('SEQUENCE_')
            shot = os.getenv('SHOT_')
            openPath = '/jobs/%s/sequences/%s/%s' % (show, seq, shot)
            browsedImagePath = str(QtWidgets.QFileDialog.getOpenFileName(self, "Select uv texture file", directory=openPath,
                                                               filter="Image Files (*.jpg *.tif *.tga *.bmp *.png)"))
            checker_name = "uvTools_checker3"
            checker_tex_path = browsedImagePath
        else:
            print "Checker type '%s' unrecognized.  Skipping." % (checker_type)
            return

        cmds.undoInfo(openChunk=True)
        if not cmds.objExists(checker_name):
            lambert, checker, uvPlacement = self.setupShader(checker_name, u, v, checker_tex_path)
        cmds.select(sel)
        mel.eval('hyperShade -assign %s' % (checker_name))
        cmds.undoInfo(closeChunk=True)

    def applyRepeats(self):
        """
            DESCRIPTION
                Procedure to change the uv repeats for the texture which is applied
                to the selected geometry

        """
        sel, u, v = self.getSelectionAndUVs(0)
        if sel:
            for node in sel:
                try:
                    shapeNode = cmds.listRelatives(node, s=True)
                    sg =cmds.connectionInfo(shapeNode[0] + '.instObjGroups[0]', destinationFromSource=True)[0].split('.')[0]
                    mat = cmds.connectionInfo(sg + '.surfaceShader', sourceFromDestination=True).split('.')[0]
                    colourInput = cmds.connectionInfo(mat + '.color', sourceFromDestination=True).split('.')[0]
                    uvNode = cmds.connectionInfo(colourInput + '.uvFilterSize', sourceFromDestination=True).split('.')[0]
                    cmds.setAttr(uvNode + '.repeatU', u)
                    cmds.setAttr(uvNode + '.repeatV', v)
                except:
                    print 'Could not change UV repeats for %s' % node
                    pass
        else:
            warn = 'Nothing selected'
            QtWidgets.QMessageBox.warning(self, 'Error', warn)

    def setupShader(self, name, u, v, texPath=''):
        """
            DESCRIPTION
                Procedure to create a lambert shader and assign a texture
                file to its colour attribute. If no texture file is specified
                use the maya checker pattern
            ARGS
            ----------------------------------------------------------------
            name = str name to assign to the shader,file,place2dTexture
            u = float repeats in u
            v = float repeats in v
            texPath = str full path to texture image
            ----------------------------------------------------------------
            RETURNS
                lambert str
                checker str
                uvPlacement str

        """
        lambert = cmds.shadingNode('lambert', n=name, asShader=True)
        uvPlacement = cmds.shadingNode('place2dTexture', n=name + '_place2dTexture', asUtility=True)
        cmds.setAttr(uvPlacement + '.repeatU', u)
        cmds.setAttr(uvPlacement + '.repeatV', v)
        if texPath:
            file = cmds.shadingNode('file', n=name + '_file', asTexture=True)


            ## connect uvPlacement node to file node
            cmds.connectAttr(uvPlacement + '.coverage', file + '.coverage', f=True)
            cmds.connectAttr(uvPlacement + '.translateFrame', file + '.translateFrame', f=True)
            cmds.connectAttr(uvPlacement + '.rotateFrame', file + '.rotateFrame', f=True)
            cmds.connectAttr(uvPlacement + '.mirrorU', file + '.mirrorU', f=True)
            cmds.connectAttr(uvPlacement + '.mirrorV', file + '.mirrorV', f=True)
            cmds.connectAttr(uvPlacement + '.stagger', file + '.stagger', f=True)
            cmds.connectAttr(uvPlacement + '.wrapU', file + '.wrapU', f=True)
            cmds.connectAttr(uvPlacement + '.wrapV', file + '.wrapV', f=True)
            cmds.connectAttr(uvPlacement + '.repeatUV', file + '.repeatUV', f=True)
            cmds.connectAttr(uvPlacement + '.offset', file + '.offset', f=True)
            cmds.connectAttr(uvPlacement + '.rotateUV', file + '.rotateUV', f=True)
            cmds.connectAttr(uvPlacement + '.noiseUV', file + '.noiseUV', f=True)
            cmds.connectAttr(uvPlacement + '.vertexUvOne', file + '.vertexUvOne', f=True)
            cmds.connectAttr(uvPlacement + '.vertexUvTwo', file + '.vertexUvTwo', f=True)
            cmds.connectAttr(uvPlacement + '.vertexUvThree', file + '.vertexUvThree', f=True)
            cmds.connectAttr(uvPlacement + '.vertexCameraOne', file + '.vertexCameraOne', f=True)
            cmds.connectAttr(uvPlacement + '.outUvFilterSize', file + '.uvFilterSize', f=True)
            cmds.connectAttr(uvPlacement + '.outUV', file + '.uv', f=True)

            ## connect file node to shader
            cmds.connectAttr(file + '.outColor', name + '.color', f=True)

            cmds.setAttr(file + '.fileTextureName', texPath, type='string')

            return lambert, file, uvPlacement

        else:
            checker = cmds.shadingNode('checker', n=name + '_checker', asTexture=True)
            ## connect uvPlacement node to checker node
            cmds.connectAttr(uvPlacement + '.outUV', checker + '.uvCoord', f=True)
            cmds.connectAttr(uvPlacement + '.outUvFilterSize', checker + '.uvFilterSize', f=True)

            ## connect checker node to shader
            cmds.connectAttr(checker + '.outColor', name + '.color', f=True)

            return lambert, checker, uvPlacement

    def getUvBoundingBoxComponents(self, objects):
        """
            Return the UV bounding box for selected geometry in ((umin, umax), (vmin, vmax))
        """
        cmds.select(objects)
        return cmds.polyEvaluate(bc2=True)

    def getUvBoundingBox(self, objects):
        """
            Return the UV bounding box for selected geometry in ((umin, umax), (vmin, vmax))
        """
        cmds.select(objects)
        return cmds.polyEvaluate(b2=True)

    def getUvShellForPoint(self, point):
        cmds.select(point)
        cmds.polySelectConstraint(type=0)
        cmds.polySelectConstraint(shell=1, border=0, mode=2)
        selection = cmds.ls(sl=True, flatten=True)
        cmds.polySelectConstraint(sh=0, bo=0, m=0)
        return cmds.ls(sl=True)

    def getUvShellsForObjects(self, objects):
        """ return a list of UV shells for a given node """
        faces = cmds.polyListComponentConversion(objects, tf=True)
        faces = cmds.ls(faces, fl=True)
        shells = []
        while (faces):
            cmds.select(faces[0])
            cmds.polySelectConstraint(type=0)
            cmds.polySelectConstraint(shell=1, border=0, mode=2)
            selection = cmds.ls(sl=True, flatten=True)
            cmds.polySelectConstraint(sh=0, bo=0, m=0)
            shells.append(cmds.ls(sl=True))
            faces = list(set(faces).difference(selection))
        return shells

    def getUvShellsForSelected(self):
        selected = cmds.ls(sl=True)
        shells = self.getUvShellsForObjects(selected)
        cmds.select(selected, ne=True)
        return shells

    def getUvsForObjects(self, objects):
        uvs = cmds.polyListComponentConversion(objects, tuv=True)
        return uvs

    def offsetUV(self, objects, u, v):
        uvs = self.getUvsForObjects(objects)
        cmds.select(uvs)
        cmds.polyEditUVShell(u=u, v=v, relative=True)

    def alignUvCallback(self, angle=0):
        def getAngle(u0, v0, u1, v1):
            [u0, v0] = cmds.polyEditUV(uv[0], q=True)
            [u1, v1] = cmds.polyEditUV(uv[1], q=True)
            u = u1 - u0
            v = v1 - v0
            if u == 0:
                u = 0.00000000000001
            current_angle = math.degrees(math.atan(v / u))
            if u > 0 and v > 0:
                pass
            elif u > 0 and v < 0:
                current_angle += 360
            elif u < 0 and v <= 0:
                current_angle += 180
            elif u < 0 and v > 0:
                current_angle += 180
            return current_angle

        cmds.undoInfo(openChunk=True)
        # selection either needs to be a single edge or two UVs
        selection = cmds.ls(sl=True, flatten=True)
        uv = None
        warn = ""
        if len(selection) == 2 and re.search("\.map\[[0-9]+\]$", selection[0]) and re.search("\.map\[[0-9]+\]$",
                                                                                             selection[1]):
            uv = [selection[0], selection[1]]
        elif len(selection) == 1 and re.search("\.e\[[0-9]+\]$", selection[0]):
            uv = cmds.ls(cmds.polyListComponentConversion(selection[0], tuv=True), flatten=True)

        if uv and len(uv) != 2:
            warn = "  Your selection resulted in more than two UVs since it was a border edge."
            uv = None

        if not uv:
            QtWidgets.QMessageBox.warning(None, "Error",
                                "<html>Invalid selection for alignment.  Selection must be a single edge or two UVs." + warn)
            return

        uv.sort()
        [u0, v0] = cmds.polyEditUV(uv[0], q=True)
        [u1, v1] = cmds.polyEditUV(uv[1], q=True)
        current_angle = getAngle(u0, v0, u1, v1)
        pivot_u = (u0 + u1) * 0.5
        pivot_v = (v0 + v1) * 0.5
        rotate_angle = angle - current_angle
        cmds.select(uv)
        cmds.polyEditUVShell(angle=rotate_angle, pivotU=pivot_u, pivotV=pivot_v)
        # debug
        [u0, v0] = cmds.polyEditUV(uv[0], q=True)
        [u1, v1] = cmds.polyEditUV(uv[1], q=True)
        final_angle = getAngle(u0, v0, u1, v1)

        cmds.select(selection, ne=True)
        cmds.undoInfo(closeChunk=True)

    def mirrorUvCallback(self, scale_u, scale_v):
        cmds.undoInfo(openChunk=True)
        objects = cmds.ls(sl=True)
        retval = self.areObjectsInSingleTile(objects)
        if not retval:
            print "Cannot move... UVs span more than one tile."
            return
        umin, umax, vmin, vmax = retval
        pivot_u = int(math.floor(umin)) + 0.5
        pivot_v = int(math.floor(vmin)) + 0.5
        uvs = cmds.polyListComponentConversion(objects, tuv=True)
        cmds.select(uvs)
        cmds.polyEditUVShell(pivotU=pivot_u, pivotV=pivot_v, scaleU=scale_u, scaleV=scale_v)
        cmds.select(objects, ne=True)
        cmds.undoInfo(closeChunk=True)

    def offsetUVCallback(self, u, v):
        selected_objects = cmds.ls(sl=True)
        objects = selected_objects
        uv_objects = [object for object in selected_objects if re.search("\.map\[.*\]$", object)]
        if uv_objects:
            objects = uv_objects
        if not objects: return
        self.offsetUV(objects, u, v)
        if self.wrap_around_checkbox.isChecked():
            ((umin, umax), (vmin, vmax)) = self.getUvBoundingBox(objects)
            if umin < 0 or umax >= 10:
                uvs = cmds.polyListComponentConversion(objects, tuv=True)
                shells = self.getUvShellsForObjects(uvs)
                for shell in shells:
                    ((umin, umax), (vmin, vmax)) = self.getUvBoundingBoxComponents(shell)
                    if umin < 0 or umax >= 10:
                        u_new = int(math.floor(umin)) % 10
                        v_new = int(math.floor(vmin)) + (int(math.floor(umin)) / 10)
                        relative_u = u_new - int(math.floor(umin))
                        relative_v = v_new - int(math.floor(vmin))
                        self.offsetUV(shell, relative_u, relative_v)

        cmds.select(selected_objects, ne=True)

    def setUVPosition(self, objects, u, v):
        """
            DESCRIPTION
                Procedure to offset the uv shell for the selection
        """
        #print "Checking set UV position for", objects
        old_sel = cmds.ls(sl=True)

        retval = self.areObjectsInSingleTile(objects)
        if not retval:
            print "Cannot move... UVs span more than one tile."
            return
        umin, umax, vmin, vmax = retval

        relative_u = u - int(math.floor(umin))
        relative_v = v - int(math.floor(vmin))
        self.offsetUV(objects, relative_u, relative_v)

    def isSingleTile(self, min_coord, max_coord):
        ''' we need something a little complicated because 1.0 can
        be part of UDIM 1001 or 1002, etc '''
        if (1 >= (int(math.ceil(max_coord) - math.floor(min_coord)))):
            return True
        else:
            return False

    def areObjectsInSingleTile(self, objects):
        ((umin, umax), (vmin, vmax)) = self.getUvBoundingBox(objects)
        if not self.isSingleTile(umin, umax) or not self.isSingleTile(vmin, vmax):
            ((umin, umax), (vmin, vmax)) = self.getUvBoundingBoxComponents(objects)
            if not self.isSingleTile(umin, umax) or not self.isSingleTile(vmin, vmax):
                QtWidgets.QMessageBox.warning(None, "Error", "UVs span more than one tile, cannot perform operation.")
                return False
        return umin, umax, vmin, vmax

    def setUdimPositionCallback(self):
        """
            DESCRIPTION
                Procedure to offset the uv shell for the selection
        """
        cmds.undoInfo(openChunk=True)
        sel, udim = self.getSelectionAndUdim()

        retval = self.areObjectsInSingleTile(sel)
        if not retval:
            print "Cannot move... UVs span more than one tile."
            return
        umin, umax, vmin, vmax = retval

        du, dv = udimToUv(udim)
        self.setUVPosition(sel, du, dv)

        cmds.select(sel, replace=True, ne=True)
        cmds.undoInfo(closeChunk=True)

    def setUVPositionCallback(self):
        """
            DESCRIPTION
                Procedure to offset the uv shell for the selection
        """
        cmds.undoInfo(openChunk=True)
        sel, du, dv = self.getSelectionAndUVs(1)

        retval = self.areObjectsInSingleTile(sel)
        if not retval:
            print "Cannot move... UVs span more than one tile."
            return
        umin, umax, vmin, vmax = retval

        self.setUVPosition(sel, du, dv)

        cmds.select(sel, replace=True, ne=True)
        cmds.undoInfo(closeChunk=True)

    def resetOffsets(self):
        sel, u, v = self.getSelectionAndUVs(1)
        self.uSpinBox2.setValue(0)
        self.vSpinBox2.setValue(0)

        self.setUVPosition()

        self.uSpinBox2.setValue(u)
        self.vSpinBox2.setValue(v)

    def uvRetainComponentSpacingCallback(self):
        """
        Callback that uses the checkbox value to set the retain component
        spacing value.
        """
        value = self.component_spacing_checkbox.isChecked()
        self.setUvRetainComponentSpacingValue(value)

    def getUvRetainComponentSpacingValue(self):
        """
        Return the value of retain component spacing.
        """
        value = cmds.texMoveContext("texMoveContext", q=True, snapComponentsRelative=True)
        return value

    def setUvRetainComponentSpacingValue(self, value):
        """
        If you have "retain component spacing" on and snap UVs to
        something, it only snaps the pivot and maintains the relative UV
        spacing.  If this is False, then all of the UVs collapse to the
        point you're snapping to otherwise.
        """
        cmds.texMoveContext("texMoveContext", e=True, snapComponentsRelative=value)
        self.getUvRetainComponentSpacingValue()

    def layOutPieces(self, direction):
        """
        Lay out the selected pieces in UV space using their bounding boxes
        to ensure no overlaps.  The spacing option determines how much
        spacing can exist between each shell.
        """
        # TODO: check the selection for any non-object (UV) selections.
        # convert selection to UV shells?

        cmds.undoInfo(openChunk=True)

        sel = cmds.ls(sl=True)
        spacing = self.getSpacingValue()
        u = spacing * 0.5
        v = spacing * 0.5
        num_cols = 1.0
        meshes = cmds.ls(sel[0], dag=True, type="mesh", noIntermediate=True)
        ((umin, umax), (vmin, vmax)) = self.getUvBoundingBox(meshes)
        usize = (umax - umin) + spacing
        vsize = (vmax - vmin) + spacing

        #if direction == DIRECTION_BOX:
        num_items = float(len(sel))
        num_cols = round(math.sqrt(num_items * vsize / usize))

        col = 0
        for piece in sel:
            meshes = cmds.ls(piece, dag=True, type="mesh", noIntermediate=True)
            ((umin, umax), (vmin, vmax)) = self.getUvBoundingBox(meshes)
            if direction == DIRECTION_HORIZONTAL:
                offset_u = u - umin
                offset_v = v - vmin
                self.offsetUV(piece, offset_u, offset_v)
                u += (umax - umin) + spacing
            elif direction == DIRECTION_VERTICAL:
                self.offsetUV(piece, u - umin, v - vmin)
                v += (vmax - vmin) + spacing
            elif direction == DIRECTION_BOX:
                col += 1
                self.offsetUV(piece, u - umin, v - vmin)
                if col >= num_cols:
                    u = spacing * 0.5
                    v += (vmax - vmin) + spacing
                    col = 0
                else:
                    u += (umax - umin) + spacing

        cmds.select(sel, ne=True)
        cmds.undoInfo(closeChunk=True)

    def getSpacingValue(self, value=None):
        if value == None:
            spacing = float(self.spacingSpinBox.value())
        else:
            spacing = float(value)
        return spacing

    def clearShaders(self):
        """
            DESCRIPTION
                Procedure to assign lambert1 to all objects that have the
                uvTools_checker shaders and then delete all the uvTools_checker
                shaders and associated shading nodes
        """
        cmds.undoInfo(openChunk=True)
        shaderList = ['uvTools_checker1', 'uvTools_checker2', 'uvTools_checker3']
        for shader in shaderList:
            if cmds.objExists(shader):
                cmds.hyperShade(o=shader)
                assigned = cmds.ls(sl=True)
                if assigned:
                    mel.eval('hyperShade -assign lambert1')
                cmds.delete(shader)
                if cmds.objExists(shader + 'SG'):
                    cmds.delete(shader + 'SG')
                if cmds.objExists(shader + '_file'):
                    cmds.delete(shader + '_file')
                if cmds.objExists(shader + '_checker'):
                    cmds.delete(shader + '_checker')
                if cmds.objExists(shader + '_place2dTexture'):
                    cmds.delete(shader + '_place2dTexture')
        cmds.undoInfo(closeChunk=True)

    def getUDIMDict(self):
        """
            DESCRIPTION
                Function to create a dictionary of udim : shape list key value pairs
                Filters out shapes which are assinged to mulitple udims
        """
        udimDict = {}
        selectedList = cmds.ls(sl=1)
        for selected in selectedList:
            shapez = cmds.listRelatives(selected, s=1)
            if shapez:
                shape = shapez[0]
                if cmds.nodeType(shape) == 'mesh':
                    udim = AttrLib.AttrLib().getAttr(shape, 'mUdim')
                    if udim:
                        if len(udim.split(',')) <= 1: # get only those shapes which don't have uvs in mulitple udims
                            if udimDict.has_key(udim):
                                udimDict[udim].append(shape)
                            else:
                                udimDict[udim] = []
                                udimDict[udim].append(shape)
                        else:
                            print 'Skipping shape %s as it has multiple UDIMs'

        return udimDict

    def pathBrowseBtnCallBack(self):
        """
            DESCRIPTION
                Call back to launch the browse dialog
        """
        openPath = self.pathLineEdt.text()
        if openPath == '':
            openPath = os.getenv('HOME')
        elif not os.path.isdir(openPath):
            openPath = os.getenv('HOME')
        browsedExportPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select directory to export objs to",
                                                             directory=openPath, options=QtWidgets.QFileDialog.ReadOnly)
        if browsedExportPath:
            self.pathLineEdt.clear()
            self.pathLineEdt.setText(browsedExportPath)

    def exportBtnCallBack(self):
        """
            DESCRIPTION
                Function to export OBJs based on UDIM numbers.
                The UVs can be moved to a specific UDIM prior to exporting
        """
        exportPath = str(self.pathLineEdt.text())
        if exportPath:
            if os.path.isdir(exportPath):
                udimDict = self.getUDIMDict()
                if udimDict:
                    if not cmds.pluginInfo('objExport', q=1, l=1):
                        cmds.loadPlugin('objExport')
                    moveTOUDIM = self.moveTOUDIM.isChecked()
                    if moveTOUDIM:
                        toUDIM = self.udimSpinBox.value()
                        for key in udimDict:
                            if int(key) != int(toUDIM):
                                for shape in udimDict[key]:
                                    cmds.select(shape, r=1)
                                    self.setUdimPositionCallback()
                    for key in udimDict:
                        cmds.select(udimDict[key], r=1)
                        objPath = os.path.join(exportPath, '%s.obj' % key)
                        cmds.file(objPath, f=1, options="groups=0;ptgroups=0;materials=0;smoothing=1;normals=1",
                                  typ="OBJexport", pr=1, es=1)
                        print 'Exported : %s' % objPath
                        if moveTOUDIM: ## reset the uvs
                            self.udimSpinBox.setValue(int(key))
                            for shape in udimDict[key]:
                                cmds.select(shape, r=1)
                                self.setUdimPositionCallback()

                    if moveTOUDIM:
                        self.udimSpinBox.setValue(int(toUDIM))

        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Export path is empty')

    def uvInterSectionBtnCB(self):
        if not cmds.pluginInfo('methodCmdPlugins', q=1, l=1):
            cmds.loadPlugin('methodCmdPlugins')
        #threaded = self.threadedChkBx.isChecked()
        threaded = False
        borderOnly = self.borderOnlyUVsChkBx.isChecked()
        findAll = self.findAllChkBx.isChecked()
        tolerance = self.toleranceDSpnBx.value()

        currentSelection = cmds.ls(sl=1)
        if currentSelection:
            masterSelection = []
            tasks = len(currentSelection)
            progressDialog = QtWidgets.QProgressDialog('Working', 'Cancel', 0, 100)
            progressDialog.setCursor(QtGui.QCursor(QtCore.Qt.BusyCursor))
            progressDialog.setWindowModality(QtCore.Qt.NonModal)
            progressDialog.canceled.connect(progressDialog.cancel)
            progressDialog.setWindowTitle('Working')
            if tasks >= 25:
                progressDialog.setWindowModality(QtCore.Qt.WindowModal)
                progressDialog.forceShow()
            else:
                progressDialog.hide()
            for i in range(tasks):
                if progressDialog.wasCanceled():
                    break
                progressDialog.setLabelText("Step %s of %d" % (i + 1, tasks))
                percent = int(100 * (float(i) / (tasks)))
                progressDialog.setValue(percent)
                if threaded:
                    intersections = cmds.checkUVIntersectionThreaded(currentSelection[i], b=borderOnly, t=tolerance,
                                                                     f=findAll)
                else:
                    intersections = cmds.checkUVIntersection(currentSelection[i], b=borderOnly, t=tolerance,
                                                             f=findAll)
                if intersections:
                    masterSelection += intersections

            if masterSelection:
                cmds.select(masterSelection, r=1)
                QtWidgets.QMessageBox.information(self, 'Info', 'Selected intersecting UVs')
            else:
                QtWidgets.QMessageBox.information(self, 'Info', 'Did not find any intersecting UVs with the given parameters')
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Nothing was selected')

    def main(self):
        self.show()

