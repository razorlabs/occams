OCCAMS Studies
==============

Study management application


Getting Started
---------------

These instructions are intended for contributors only.

Configure your OCCAMS application using the instructions located at:
https://bitbucket.org/ucsdbitcore/occams

Once you've set up the platform, speciy this application in
your configuration::

  occams.apps =
      ...
      occams_studies


To install the database tables::

  > oc_initdb -c etc/development.ini

This application uses celery tasks, so make sure you are running the service::

  > celery worker --autoreload --app "occams.studies.tasks" --loglevel INFO --without-gossip --ini etc/development.ini


Configuration
-------------

TODO
