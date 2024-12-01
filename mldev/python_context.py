# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Python context module
=====================

This module provides custom tags to import python functions directly into
the experiment.

When used in a experiment spec, the experiment should be loaded in ``EXPERIMENT`` environment.
No in the ``MLDEV`` environment as by default.

"""

import importlib.util as import_lib
import os

from mldev.experiment_tag import _scalar_representer, _scalar_loader, experiment_tag
from mldev.expression import Expression


def load_function(path, module_name, object_name):
    spec = import_lib.spec_from_file_location(module_name, path)
    module = import_lib.module_from_spec(spec)
    spec.loader.exec_module(module)
    _obj = module.__getattribute__(object_name[0])
    for name in object_name[1:]:
        _sub_obj = _obj.__getattribute__(_obj, name)
        _obj = _sub_obj.__get__(_obj)

    return _obj


@experiment_tag(loader=_scalar_loader, representer=_scalar_representer, name="function")
class PythonFunction:
    """
    Use this to load a specific python function into object graph from experiment.yaml

    This is a string scalar specifying a fully qualified name of the function
    """
    def __new__(cls, *args, **kwargs):
        function_name = str(Expression(args[0]))

        file_name = function_name.split("/")[-1].split(".")[0]
        file_path = "/".join(function_name.split("/")[:-1])
        module_name = os.path.relpath(os.path.join(file_path, file_name))
        path = f"{module_name}.py"
        import_names = function_name.split("/")[-1].split(".")[1:]

        return load_function(
            path=path,
            module_name=module_name.replace("/", "."),
            object_name=import_names
        )
