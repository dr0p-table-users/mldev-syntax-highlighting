# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Experiment Tag module
=====================

This module provides facilities to define new tags for use in experiments.

See ``experiment_tag`` decorator.

"""

import yaml


def _mapping_loader(cls):
    def wrapped(loader, node):
        node_map = loader.construct_mapping(node, deep=True)
        return cls(**node_map)

    return wrapped


def _mapping_representer(cls):
    def wrapped(dumper, data):
        return dumper.represent_mapping(f"!{cls.__name__}", data.__dict__)

    return wrapped


def _scalar_representer(cls):
    def wrapped(dumper, data):
        return dumper.represent_scalar(f"!{cls.__name__}", str(data))

    return wrapped


def _scalar_loader(cls):
    def wrapped(loader, node):
        node_value = loader.construct_scalar(node)
        return cls(node_value)

    return wrapped


def experiment_tag(loader=_mapping_loader, representer=_mapping_representer, name=None, pattern=None):
    """
    Use this tag to mark classes invoked from experiment.yml

    Note: use `experiment_tag()`, not just `experiment_tag`

    :param loader: a loader (deserializer) for the specified class to pass to YAML loader
    :param representer: a representer (serializer) for the class to pass to YAML loader
    :param name: a tag name to use, will use classname if absent
    :param pattern: a regexp pattern to use when extracting from scalar strings (see also yaml.add_implicit_resolver)
    :return: wrapped class
    """

    def wrapped(cls):
        yaml.add_representer(cls, representer(cls))
        tag_name = name if name else cls.__name__
        tag_name = f"!{tag_name}"
        if pattern:
            yaml.add_implicit_resolver(tag_name, regexp=pattern)

        yaml.add_constructor(tag_name, loader(cls))
        return cls

    return wrapped
