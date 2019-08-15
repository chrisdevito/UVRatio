#!/usr/bin/python
# -*- coding: utf-8 -*-
from UVRatio.packages.Qt import QtWidgets


def show():
    """
    Shows ui in maya

    :raises: None

    :return: None
    :rtype: NoneType
    """
    from UVRatio.ui.ui import UI
    from UVRatio.ui import utils

    # prevent duplicate windows
    for widget in QtWidgets.QApplication.instance().topLevelWidgets():
        if widget.objectName() == 'UVRatio':
            widget.close()

    win = UI(utils.get_maya_window())
    win.show()
