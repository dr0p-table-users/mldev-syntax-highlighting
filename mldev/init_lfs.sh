#!/bin/bash

# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

echo "INFO:mldev: git lfs setup"

git lfs install --local
touch .gitattributes
git add -f .gitattributes

echo "INFO:mldev: git lfs setup done"