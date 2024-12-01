#!/bin/bash

# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

set -eo pipefail

# enable debug
#set -x

# ask user for missing required parameters or fail
# 0 - ask always and provide current values
# 1 - ask missing only
# 2 - do not ask, fail
# ASK_MISSING=0

# environment vars
# LOG_LEVEL=   - same as logging.*

if [ "${LOG_LEVEL}" -lt "20" ]; then
  set -x
fi

PYTHON=${PYTHON_INTERPRETER:-python3}

if [ $PYTHON = "python2" ];
then
  PYTHON_VENV="python2 -m virtualenv"
else
  PYTHON_VENV="python3 -m venv"
fi

init_venv() {
  # create virtual environment and activate it
  # it also install pip into venv
  SUB='darwin'
  if [[ "$OSTYPE" == *"$SUB"* ]]; then
    dir_name=$(greadlink -f "$1");
    else
      dir_name=$(readlink -f "$1");
  fi
  cd "$dir_name"
  if [ ! -d "./venv" ]; then
    >&2 echo "INFO:mldev:Creating Python virtual environment"
    ${PYTHON_VENV} venv
  fi

  # activate the environment
  source ./venv/bin/activate
  ${PYTHON} -m pip install --upgrade pip setuptools wheel

  # install template dependencies
  FILE=./requirements.txt
  if test -f "$FILE"; then
    >&2 echo "INFO:mldev:Installing template reqs from $FILE"
    ${PYTHON} -m pip install -r "$FILE"
  fi

}

if [ $# -eq 0 ]; then
  >&2 echo "INFO:mldev:Usage: $0 <folder> "; exit 1;
fi

>&2 echo "INFO:mldev:Setting up virtual environment"
init_venv "$1"