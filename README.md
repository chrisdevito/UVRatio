# UVRatio
Copies UV's scale based on it's ratio from worldarea to uv area

.. code-block:: python

	import sys

	module_path = "/home/cdevito/dev/Tools/maya/modules/UVRatio"

	if module_path not in sys.path:
	    sys.path.insert(1, module_path)

	import UVRatio
	reload(UVRatio)
	reload(UVRatio.api)
	reload(UVRatio.ui)
	reload(UVRatio.ui.ui)
	UVRatio.show()
