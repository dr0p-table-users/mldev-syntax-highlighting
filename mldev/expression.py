# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Expressions module
==================

This module implements parameterizable strings for use within experiment spec.

Expressions employ ``self`` variable, which corresponds to the currently executing stage.

See also ``yaml_loader.py`` module for more implementation details.

"""

import re
from collections.abc import Mapping, Iterable
from typing import Any

from simpleeval import EvalWithCompoundTypes
import json
import os

from mldev.utils import shell_escape
from mldev_config_parser import config_parser


def _default_encoder(o: Any) -> Any:
    """
    Calls ``to_json`` method of an object ``o`` if present
    Used by ``_to_json``  function in ``eval_ctx``
    :param o: object to convert
    :return: representation of an object for serialization to json
    """
    if hasattr(o, 'to_json'):
        if callable(o.to_json):
            return o.to_json()

    raise Exception(f"Cannot convert to json: {o}")


def _to_json(o, escape=True):
    s = json.dumps(o, default=_default_encoder)
    if escape:
        return shell_escape(s)
    else:
        return s


def _to_params(p):
    # try to make a dict form the object
    if isinstance(p, Mapping):
        p = p # ok
    elif isinstance(p, Iterable):
        p = dict(p) # may fail
    else:
        p = vars(p)

    s = " ".join(["--{} \"{}\"".format(str(k), str(v))
                  if not isinstance(v, bool)
                  else (" --{}".format(str(k)) if v else "")
                  for k, v in p.items()])
    return s


def _path(s):
    return os.path.abspath(str(s))


class defaultdict_v2(dict):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not default:
            self.default = lambda : None

    def __missing__(self, item):
        return self.default()

    def __contains__(self, item):
        return True


_EVAL_FUNCTIONS = {
    'json': _to_json,
    'path': _path,
    'params': _to_params
}

PARAM_PATTERN = re.compile(r'\$\{([^}^{]+)\}')


def eval_ctx(p, ctx=None, doc=None):
    """
    Evaluates an expression ``p`` in context ``ctx``

    The following variables are available for expressions:

     - ``env`` : a ``dict`` that includes ``os.environ``
       and ``MLDevSettings().environ``
       if a key is missing, ``None`` is returned to expression
     - ``_`` : a context object

    These functions are available for expressions:

     - ``json(o)`` : converts its argument ``o`` to json string
     - ``path(p)`` : expands its argument to an absolute path
     - ``params(dict)`` : converts dict to a sequence of ``--<key> <value>`` pairs

    See ``_EVAL_FUNCTIONS``

    :param ctx: context to evaluate ``p``
    :param p: expression to evaluate
    :return: result of evaluation
    """
    names = dict()
    names['stage'] = ctx
    names['self'] = ctx
    names['root'] = doc

    names['env'] = defaultdict_v2(dict())
    names['env'].update(config_parser.MLDevSettings().environ)
    names['env'].update(os.environ)

    return EvalWithCompoundTypes(functions=_EVAL_FUNCTIONS,
                       names=names).eval(p)


class Expression:
    """
    Implements a parameterizable string which values are computed at runtime
    from the currently available parameters in the context

    """

    def __init__(self, value, pattern=PARAM_PATTERN, ctx=None, doc=None):
        super().__init__()
        self.__eval_ctx__ = ctx
        self.__eval_doc__ = doc
        self.value = value
        self.params = pattern.findall(self.value)

    def __str__(self):
        result = str(self.value).strip()
        for p in self.params:
            ctx = self.__eval_ctx__() if self.__eval_ctx__ else None
            doc = self.__eval_doc__() if self.__eval_doc__ else None
            val = str(eval_ctx(p, ctx=ctx, doc=doc))
            result = str(result).replace(f'${{{p}}}', val)
        return result

    def __int__(self):
        return int(str(self))

    def __float__(self):
        return float(str(self))

    def __repr__(self):
        return f"({self.__class__.__name__})'" + self.__str__() + "'"

    def __getitem__(self, item):
        return self.__str__().__getitem__(item)

    def __iter__(self):
        return self.__str__().__iter__()

    def __eq__(self, other):
        return str(self) == other

    def __hash__(self):
        return hash(str(self))

    def to_json(self):
        return str(self)

    def __get_state__(self):
        return str(self)