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

if [ "${LOG_LEVEL}" -lt "20" ]; then
  GIT_TRACE=True
  set -x
  export GIT_TRACE
fi

expand_template_mldev() {
  GLOBIGNORE=".:.."
  mkdir -p "${1:?}"
  tmp_dir=$(mktemp -d)
  curl "https://gitlab.com/mlrep/${2}/-/archive/master/${2}-1-master.tar.gz" | tar -zx -C "${tmp_dir}"
  src_files=( "${tmp_dir:?}/${2:?}"-master-*/* )
  mv "${src_files[@]}" "${1:?}"
  rm -r "${tmp_dir:?}"
}

expand_template_github() {
  GLOBIGNORE=".:.."
  mkdir -p "${1:?}"
  tmp_dir=$(mktemp -d)
  curl -L --silent "${2}/archive/main.zip" -o "${tmp_dir}/template.zip"
  unzip "${tmp_dir}/template.zip" -d "${tmp_dir}/template-unzip"
  src_dir=( "${tmp_dir:?}/template-unzip"/* )
  src_files=( "${src_dir:?}"/* )
  mv "${src_files[@]}" "${1:?}"
  rm -r "${tmp_dir:?}"
}

expand_template_gitlab() {
  GLOBIGNORE=".:.."
  mkdir -p "${1:?}"
  tmp_dir=$(mktemp -d)
  cd "$tmp_dir" && git clone -b master --depth 1 "${2}" "${tmp_dir}/template"
  cd "$tmp_dir/template" && git archive --format=zip --output="${tmp_dir}/template.zip" HEAD
  unzip "${tmp_dir}/template.zip" -d "${tmp_dir}/template-unzip"
  src_files=( "${tmp_dir:?}/template-unzip"/* )
  mv "${src_files[@]}" "${1:?}"
  rm -rf "${tmp_dir:?}/template" "${tmp_dir:?}/template.zip" "${tmp_dir:?}/template-unzip"
}

get_template() {
  # get template
  SUB='darwin'
  if [[ "$OSTYPE" == *"$SUB"* ]]; then
    dir_name=$(greadlink -f "$1");
    else
      dir_name=$(readlink -f "$1");
  fi
  template_name="$2"
  if [ "$template_name" = "-" ]; then template_name="template-default"; fi
  >&2 echo "INFO:mldev:Setting up template <$template_name> to $dir_name"

  if [ -d "$1" ]; then >&2 echo "ERROR:mldev:Directory $dir_name already exists"; exit 1; fi

  >&2 echo "INFO:mldev:Using https://gitlab.com/mlrep/${template_name}"

  if [[ $template_name == "https://github.com"* ]]
  then
    expand_template_github "${dir_name}" "${template_name}"
  elif [[ $template_name == "https://gitlab.com"* ]]
  then
    expand_template_gitlab "${dir_name}" "${template_name}"
  else
    expand_template_mldev "${dir_name}" "${template_name}"
  fi

  cd "$dir_name"
}


if [ $# -eq 0 ]; then
  >&2 echo "INFO:mldev:Usage: $0 <folder> [<template-name>] "; exit 1;
fi

if [ -n "$2" ]; then
  >&2 echo "INFO:mldev:Configuring new experiment"
  get_template "$1" "$2"
else
  >&2 echo "INFO:mldev:Checking your git config"
fi

if [ ! -d ".mldev" ]; then
  mkdir .mldev/
  mkdir .mldev/logs
  printf "/ngrok\n/logs\n/controller\n/tensorboard\n/bot\n" > .mldev/.gitignore
fi

