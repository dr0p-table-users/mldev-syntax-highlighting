#!/bin/bash

# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[].public_url'