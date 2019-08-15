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
        pass

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
