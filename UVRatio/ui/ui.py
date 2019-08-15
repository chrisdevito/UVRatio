#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from functools import partial

from UVRatio import api
from UVRatio.packages.Qt import QtWidgets, QtCore

this_package = os.path.abspath(os.path.dirname(__file__))
this_path = partial(os.path.join, this_package)


class UI(QtWidgets.QDialog):
    """
    :class:`UI` inherits a QDialog and customizes it.
    """
    def __init__(self, parent=None):

        super(UI, self).__init__(parent)

        # Set window
        self.setWindowTitle("UVRatio")
        self.setObjectName("UVRatio")
        self.resize(450, 150)

        # Grab stylesheet
        with open(this_path("style.css")) as f:
            self.setStyleSheet(f.read())

        # Center to frame.
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Our main layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.create_layout()
        self.create_connections()
        self.create_tooltips()

        self.setLayout(self.layout)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def create_layout(self):
        """
        Creates layout.

        :raises: None

        :return: None
        :rtype: NoneType
        """
        self.source_lbl = QtWidgets.QLabel("Source ")
        self.source_lnedt = QtWidgets.QLineEdit("")
        self.source_btn = QtWidgets.QPushButton("<<")

        self.dest_lbl = QtWidgets.QLabel("Destination ")
        self.dest_lnedt = QtWidgets.QLineEdit("")
        self.dest_btn = QtWidgets.QPushButton("<<")

        self.source_ratio = QtWidgets.QLabel("Source Ratio : 1.0")
        self.dest_ratio = QtWidgets.QLabel("Destination Ratio : 1.0")

        self.doit_btn = QtWidgets.QPushButton("Copy UV Ratio")
        self.doit_btn.setMinimumHeight(40)

        self.ratio_layout = QtWidgets.QGridLayout()
        self.ratio_layout.addWidget(
            self.source_ratio, 0, 0, QtCore.Qt.AlignCenter)
        self.ratio_layout.addWidget(
            self.dest_ratio, 0, 1, QtCore.Qt.AlignCenter)

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.addWidget(self.source_lbl, 0, 0, QtCore.Qt.AlignRight)
        self.grid_layout.addWidget(self.source_lnedt, 0, 1)
        self.grid_layout.addWidget(self.source_btn, 0, 2)
        self.grid_layout.addWidget(self.dest_lbl, 1, 0, QtCore.Qt.AlignRight)
        self.grid_layout.addWidget(self.dest_lnedt, 1, 1)
        self.grid_layout.addWidget(self.dest_btn, 1, 2)

        self.layout.addLayout(self.ratio_layout)
        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(self.doit_btn)

    def create_connections(self):
        """
        Creates connections to buttons.

        :raises: None

        :return: None
        :rtype: NoneType
        """
        pass

    def create_tooltips(self):
        """
        Creates tool tips for various widgets.

        :raises: None

        :return: None
        :rtype: NoneType
        """
        pass

    def keyPressEvent(self, event):
        '''
        Override key focus issue.
        '''
        if event.key() in (QtCore.Qt.Key.Key_Shift, QtCore.Qt.Key.Key_Control):
            event.accept()
        else:
            event.ignore()
