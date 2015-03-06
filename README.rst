OCCAMS Studies
==============

Clinical research data management and analysis software.


System Requirements
-------------------

  * Python 2.7+
  * npm
    - lessc (must be installed globally, i.e. with "-g" option)
  * redis
  * PostgreSQL 9.3+


Getting Started
---------------

These instructions are intended for contributors only.

Create a virtual environment for your work::

  > virtualenv occams
  > source occams/bin/activate

Next, create the necesary directories::

  > cd occams
  > mkdir -p etc
  > mkdir -p var/exports
  > mkdir -p var/blobs
  > mkdir -p src

You'll need to git checkout each web application individually. If you are
using your own forks, change ``ucsdbitcore`` to yours. The reason we
checkout each project individually is because pip will replace all
git changes/history the next time your run pip install on a git
repo, which can lead you to lose a lot of work and sanity::

  > cd src
  > git clone git@bitbucket.org:ucsdbitcore/occams.datastore.git
  > git clone git@bitbucket.org:ucsdbitcore/occams.forms.git
  > git clone git@bitbucket.org:ucsdbitcore/occams.accounts.git
  > git clone git@bitbucket.org:ucsdbitcore/occams.roster.git
  > git clone git@bitbucket.org:ucsdbitcore/occams.studies.git

Now that your projects are checked out, copy and update the ``requirements-sample.ini``
found in the ``occams.studies`` project directory.::

  > cd $VIRTUAL_ENV
  > cp src/occams.studies/requirements-sample.txt requirements.txt
  > vim requirements.txt
  > pip install -U -r requirements.txt

Once everything is installed you'll need to configure the application with
your desired development environment settings::

  > cp src/occams.studies/development-sample.ini etc/development.ini
  > cp src/occams.studies/who-sample.ini etc/who.ini
  > vim etc/development.ini
  > vim etc/who.ini

Install the database tables::

  > oc_initdb -c etc/development.ini


Start the web service::

  > gunicorn --reload --paste etc/development.ini


In another terminal, start the celery worker, this handles all the exports::

  > celery worker --autoreload --app "occams.studies.tasks" --loglevel INFO --without-gossip --ini etc/development.ini
