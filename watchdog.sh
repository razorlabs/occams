#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

watchmedo shell-command \
  --patterns="*.py" \
  --recursive \
  --command="kill -HUP `cat /tmp/gunicorn.pid`" \
  $DIR

