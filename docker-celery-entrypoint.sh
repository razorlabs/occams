#!/usr/bin/env bash

#
# Entry point script for Celery service
#
# * Waits until database tables have been setup by the application service
# * Starts celery workers
#

CONFIG_FILE=develop.ini


if [[ ! $(alembic -c $CONFIG_FILE current &>/dev/null) ]]; then

  echo "Database has not been created yet, waiting for app to create it..."
  sleep 3

fi

celery worker --app occams --loglevel INFO --without-gossip --ini $CONFIG_FILE
