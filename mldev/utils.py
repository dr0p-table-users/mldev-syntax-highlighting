# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Execution utils module
======================

This module provides utils to execute internal mldev command from shell scripts
and external scripts from stages.

"""

import os
import signal
import subprocess
from mldev_config_parser.config_parser import MLDevSettings
from mldev import logger
import time
from pathlib import Path


def exec_tool_command(cmdline, extra="mldev", environ=None):
    """
    Executes the given tool command :param cmdline: with shell.

    See ``exec_command`` for more details
    :param cmdline: command to execute (relative to ``install_dir``)
    :param environ: additional environment for the tool command
    :return: instance of ``CompletedProcess``
    """

    install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    tool_dir = os.path.join(install_dir, extra)
    return exec_command(f"{tool_dir}/{cmdline}", env=environ)


def shell_quote(s: str):
    """
    Escapes and quotes string ``s``

    :param s:
    :return:
    """
    return f"\"{shell_escape(s)}\""


def shell_escape(s: str, shell_symbols="\"\'"):
    """
    If any control symbols - prepend '\'
    Double '\' to '\\'
    :param s: a string to escape
    :param shell_symbols: a string with control characters to escape
    :return: escaped string
    """
    s = s.replace("\\", "\\\\")

    for c in shell_symbols:
        s = s.replace(c, '\\' + c)

    return f"{s}"


def cast_values_to_strs(dictionary):
    result = dict()
    for k in dictionary:
        result[k] = str(dictionary[k])

    return result


def exec_command(cmdline, env=None, capture=False):
    """
    Executes the given :param cmdline: with shell.
    Passes current ''os.environ'' to the command.

    Calls ''setenv.sh'' script before running the command

    Raises exception if subordinate command fails
    :param cmdline: command line to execute
    :param env: additional environment for command
    :param capture: if True, then capture output in ``CompletedProcess.stdout``
    :return: instance of ``CompletedProcess``
    """

    environ = dict()
    environ.update(cast_values_to_strs(os.environ))
    environ.update(cast_values_to_strs(MLDevSettings().environ))
    if env:
        environ.update(cast_values_to_strs(env))

    kwargs = {
           'shell': True,
           'check': True,
           'universal_newlines': True,
           'env': environ
        }

    if capture:
        kwargs.update(
            {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT
            }
        )

    logger.debug(f"Running command: '{cmdline}' with kwargs={kwargs}")
    return subprocess.run(f'{cmdline}', **kwargs)


def prepare_experiment_command(cmdline, env=None):
    """
    Makes a single string to run the given :param cmdline: with shell.
    Passes :param env: to the command by prepending with ``export``.

    :param cmdline: command line to execute
    :param env: additional environment to pass
    :return: a cmdline that runs in venv
    """

    if not env:
        env = dict()
    # env.update(cast_values_to_strs(os.environ))
    # env.update(cast_values_to_strs(MLDevSettings().environ))
    env = cast_values_to_strs(env)

    envline = "".join([f'export {k}={shell_quote(v)}; ' for k, v in env.items()])
    venv_path = "./venv/bin/activate"
    call_line = f"source \"{venv_path}\" && {cmdline}"
    return f'/bin/bash -c ' \
           f"'{envline + call_line}'"


def check_kill_process(pstring):
    """
    TODO docs

    :param pstring: 
    "returns:
    """
    # todo use check_output or similar
    # todo kill only those that started by mldev
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        os.kill(int(pid), signal.SIGKILL)


def touch_file(file, is_dir=False):
    try:
        if not is_dir:
            dir_name = os.path.dirname(os.path.abspath(file))
            os.makedirs(dir_name, exist_ok=True)
            with open(file, 'a'):
                ...
        else:
            os.makedirs(file, exist_ok=True)
    except OSError as e:
        logger.warning(e)


def get_path_times(path, min_ts=time.time(), max_ts=0):
    # this function currently calculates times from all files in dir

    missing = False
    try:
        file_ts = os.path.getmtime(str(path))
        min_ts = min(file_ts, min_ts)
        max_ts = max(file_ts, max_ts)

        for f in Path(str(path)).rglob("*"):
            try:
                file_ts = os.path.getmtime(str(f))
                min_ts = min(file_ts, min_ts)
                max_ts = max(file_ts, max_ts)
            except OSError:
                pass
    except OSError:
        missing = True

    return min_ts, max_ts, missing


def set_path_times(path, times=(time.time(), time.time())):
    # this function currently updates times for all files in dir
    # does not work :(
    missing = False
    try:
        os.utime(str(path), times)

        for f in Path(str(path)).rglob("*"):
            try:
                os.utime(str(f), times)
            except OSError:
                pass
    except OSError:
        missing = True

    return not missing