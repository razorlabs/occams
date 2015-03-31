OCCAMS
======

Clinical research data management and analysis software.


System Requirements
-------------------

  * Python 2.7+
  * npm
    - bower
    - lessc (must be installed globally, i.e. with "-g" option)
  * redis
  * PostgreSQL 9.3+


Getting Started
---------------

These instructions are intended for contributors only.

Make sure you have the required node packages installed::

  > npm install -g bower
  > npm install -g lessc

Create a virtual environment for your work::

  > virtualenv occams
  > source occams/bin/activate

Next, create the necesary directories::

  > cd occams
  > mkdir -p etc
  > mkdir -p var/exports
  > mkdir -p var/blobs
  > mkdir -p src

You'll need to git checkout the web application. If you are
using your own forks, change ``ucsdbitcore`` to yours. The reason we
checkout each project individually is because pip will replace all
git changes/history the next time your run pip install on a git
repo, which can lead you to lose a lot of work and sanity::

  > cd src
  > git clone git@bitbucket.org:YOURID/occams

If you plan on working on add-ons, it is recommended you install the
following as well::

  > git clone git@bitbucket.org:YOURID/occams_datastore
  > git clone git@bitbucket.org:YOURID/occams_forms
  > git clone git@bitbucket.org:YOURID/occams_accounts
  > git clone git@bitbucket.org:YOURID/occams_roster
  > git clone git@bitbucket.org:YOURID/occams_studies
  > git clone git@bitbucket.org:YOURID/occams_lims


Now that your projects are checked out, copy and update the ``requirements-sample.txt``
found in the ``occams`` project directory.::

  > cd $VIRTUAL_ENV
  > cp src/occams/requirements-sample.txt requirements.txt
  > vim requirements.txt
  > pip install -U -r requirements.txt

Once everything is installed you'll need to configure the application with
your desired development environment settings::

  > cp src/occams.studies/development-sample.ini etc/development.ini
  > cp src/occams.studies/who-sample.ini etc/who.ini
  > vim etc/development.ini
  > vim etc/who.ini

Install the appropriate database tables::

  > oc_initdb -c etc/development.ini


Start the web service::

  > gunicorn --reload --paste etc/development.ini


If you applications are using asynchronous tasks, you'll need to start the
celery worker::

  > celery worker --autoreload --app "occams.studies.tasks" --loglevel INFO --without-gossip --ini etc/development.ini
