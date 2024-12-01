# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Yaml Loader module
==================

This module defines a custom Yaml loader that support custom types

Expressions employ ``self`` variable, which corresponds to the currently executing stage.

"""

import contextlib
import os
import threading
from collections.abc import Mapping
from typing import Sequence, Set

import yaml

from mldev import expression
from mldev import logger
from mldev.experiment_tag import experiment_tag, _scalar_loader, _scalar_representer
from mldev_config_parser import config_parser


@experiment_tag(loader=_scalar_loader, representer=_scalar_representer,
                name="eval", pattern=expression.PARAM_PATTERN)
class ExpressionEval(expression.Expression):
    ...


@experiment_tag(loader=_scalar_loader, representer=_scalar_representer,
                name="line")
class MultiLine(expression.Expression):

    def __init__(self, value, pattern=expression.PARAM_PATTERN, ctx=None, doc=None):
        # remove all newlines from the value
        value = str(value).replace("\n", "").replace("\r", "")
        super().__init__(value, pattern, ctx, doc)


class YamlLoaderWithEnvVars:
    """
    Class that loads yaml file and substitutes variables defined as ${var_name} in config
    from env (export var_name=var_value) or from /home/{username}/.config/mldev, if variables were
    passed as env vars in previous launches.
    """

    def __init__(self, path):
        self.experiment_file_path = os.path.abspath(path)
        self.mldev_settings = config_parser.MLDevSettings()
        self.tag = "tag:yaml.org,2002:str"
        self.pattern_for_params = expression.PARAM_PATTERN
        self.loader = yaml.FullLoader

    def load_config(self):
        """
        This method loads config with path self.experiment_file_path and returns dict
        with substituted variables.
        """
        yaml.add_constructor(self.tag, self._substitute_variables)
        with open(self.experiment_file_path, "r", encoding="utf8") as f:
            doc = yaml.load(f, Loader=yaml.FullLoader)
            for t in doc.items():
                # assign eval_ctx
                # todo this loop assumes contexts are first-level in doc
                # todo which is not true (see below stage_context)
                ctx = t[1]
                _bind_eval_ctx(t, ctx=ctx, doc=doc)

        return doc

    def _get_var_from_settings(self, var_name):
        if var_name in self.mldev_settings.environ:
            return self.mldev_settings.environ[var_name]
        return None

    def _set_var_to_settings(self, var_name, var_value):
        self.mldev_settings.environ[var_name] = var_value

    def _get_var_from_env_or_settings(self, var_name):
        var_value = os.getenv(var_name)
        if var_value is None:
            var_value = self._get_var_from_settings(var_name)
            if var_value is None:
                logger.debug(f"{var_name} is not defined in env or settings "
                             f"will try to load from attributes")

        return var_value

    def _substitute_variables(self, loader, node):
        value = loader.construct_scalar(node)
        match = self.pattern_for_params.findall(value)
        if match:
            return expression.Expression(value)
        return value


if '__threading_local' not in globals():
    __threading_local = threading.local()


@contextlib.contextmanager
def stage_context(stage):
    local_ctx = __threading_local
    if hasattr(local_ctx, 'stage'):
        prev_stage = local_ctx.stage

    local_ctx.stage = stage
    try:
        yield stage
    finally:
        if 'prev_stage' in locals():
            local_ctx.stage = prev_stage
        else:
            delattr(local_ctx, 'stage')


def _bind_eval_ctx(target, ctx, doc):

    def get_context():
        local_ctx = __threading_local
        if hasattr(local_ctx, 'stage'):
            return local_ctx.stage
        else:
            return None

    if isinstance(target, expression.Expression):
        if hasattr(target, '__eval_ctx__'):
            if target.__eval_ctx__ is None:
                target.__eval_ctx__ = get_context
        if hasattr(target, '__eval_doc__'):
            if target.__eval_doc__ is None:
                target.__eval_doc__ = lambda: doc
    elif isinstance(target, Mapping):
        for s in target.items():
            _bind_eval_ctx(s, ctx, doc)
    elif (isinstance(target, Sequence) or isinstance(target, Set)) \
         and not isinstance(target, str):
        for s in iter(target):
            _bind_eval_ctx(s, ctx, doc)
    else:
        if not hasattr(target, '__dict__'):
            return
        for attr in target.__dict__.items():
            _bind_eval_ctx(attr, ctx, doc)
