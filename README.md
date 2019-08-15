# UVRatio
Copies UV's scale based on it's ratio from worldarea to uv area. Currently only works on polygonal meshes.

    import sys
    module_path = "/home/cdevito/dev/Tools/maya/modules/UVRatio"

    if module_path not in sys.path:
        sys.path.insert(1, module_path)

    import UVRatio

    try:
        reload(UVRatio)
        reload(UVRatio.ui)
        reload(UVRatio.ui.ui)
        reload(UVRatio.api)
    except:
        pass

    UVRatio.show()
