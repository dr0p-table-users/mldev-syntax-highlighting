#!/bin/bash

# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

set -eo pipefail

# enable debug
# set -x

# ask user for missing required parameters or fail
# 0 - ask always and provide current values
# 1 - ask missing only
# 2 - do not ask, fail
# ASK_MISSING=0

# environment vars
# LOG_LEVEL=   - same as logging.*

check_init_git() {
  GIT_PRESENT=$(git status 2>/dev/null 1>&2; echo $?)

  # init git
  if [ "0" != ${GIT_PRESENT} ];
  then
    git init
  fi

  if [ -z "$(git remote 2>/dev/null || true)" ];
  then
    read -rp "(mldev) Please specify your new remote url (empty to skip): " git_remote

    if [ ! -z "$git_remote" ]; then
      git remote add origin "$git_remote"
    fi
  fi

  refresh_git

  if [ "1" = "$1" ];
  then
    GLOBIGNORE=.:.. && git add * .* || true
    git commit -m "(mldev) Experiment initial commit" || true
  fi
}

refresh_git() {
  _set_e=false
  if [ -o errexit ]; then
    set +e
    _set_e=true
  fi

  user_name="$(git config user.name)"
  user_email="$(git config user.email)"

  if [ -z "$user_name" ] || [ -z "$user_email" ]; then
    echo "(mldev) Your Git is not configured, user.name or user.email is not set"
    read -eri "$user_name" -p "(mldev) Git username: " user_name
    read -ei "$user_email" -p "(mldev) Git email: " user_email

    git config user.name "$user_name"
    git config user.email "$user_email"
  fi
  if [ "$_set_e" == true ]; then set -e; fi
}

if [ $# -ne 1 ]; then
  >&2 echo "INFO:mldev:Usage: $0 <do_commit>"; exit 1;
fi

check_init_git $1

if [ -n "$2" ]; then
  >&2 echo "INFO:mldev:"
  >&2 echo "INFO:mldev:You may want to push your local code to repo ${git_remote}"
  >&2 echo "INFO:mldev:Type:"
  >&2 echo "INFO:mldev:   cd $(pwd)"
  >&2 echo "INFO:mldev:   git push --set-upstream origin master"
  >&2 echo "INFO:mldev: "
fi