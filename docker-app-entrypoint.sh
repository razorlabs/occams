#!/usr/bin/env bash

#
# Entry point script for main WSGI application service
#
# * Configures static assets (in case source code is mounted for development)
# * Installs database tables
# * Starts gunicorn
#

export CONFIG_FILE=${CONFIG_FILE:-develop.ini}
export ALEMBIC_FILE=${ALEMBIC_FILE:-alembic.ini}


if [[ ! -d "./occams/static/bower_components" ]]; then

  echo "Assets not built yet, running bower install"
  bower install

fi


if [[ ! $(alembic current &>/dev/null) ]]; then

  echo "Database has not been created yet, running initdb"
  occams_initdb ${ALEMBIC_FILE}

fi


gunicorn --no-sendfile --paster ${CONFIG_FILE}
