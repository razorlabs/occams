#!/usr/bin/env bash

#
# Entry point script for Celery service
#
# * Waits until database tables have been setup by the application service
# * Starts celery workers
#

CONFIG=${CONFIG:-develop.ini}
LOGLEVEL=${LOGLEVEL:-INFO}

if [[ ! $(alembic current &>/dev/null) ]]; then

  echo "Database has not been created yet, waiting for app to create it..."
  sleep 3

fi

C_FORCE_ROOT=1 celery worker -E -A occams.tasks --loglevel ${LOGLEVEL} --ini ${CONFIG}
