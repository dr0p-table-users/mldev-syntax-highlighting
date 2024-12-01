#!/bin/bash

# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

set -euo pipefail

dir_name=${1:-.mldev/ngrok}
>&2 echo "INFO:mldev:Installing ngrok to $dir_name"

cd $dir_name
NGROK_PACKAGENAME=$(curl --silent --remote-name --remote-header-name --write-out "%{filename_effective}" \
               https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip)

unzip "./${NGROK_PACKAGENAME}" && rm "./${NGROK_PACKAGENAME}"
>&2 echo "INFO:mldev:Done with ngrok"