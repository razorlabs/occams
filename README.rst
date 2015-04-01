
::

    .d88888b.   .d8888b.   .d8888b.        d8888 888b     d888  .d8888b.
   d88P" "Y88b d88P  Y88b d88P  Y88b      d88888 8888b   d8888 d88P  Y88b
   888     888 888    888 888    888     d88P888 88888b.d88888 Y88b.
   888     888 888        888           d88P 888 888Y88888P888  "Y888b.
   888     888 888        888          d88P  888 888 Y888P 888     "Y88b.
   888     888 888    888 888    888  d88P   888 888  Y8P  888       "888
   Y88b. .d88P Y88b  d88P Y88b  d88P d8888888888 888   "   888 Y88b  d88P
    "Y88888P"   "Y8888P"   "Y8888P" d88P     888 888       888  "Y8888P"


**O**pen Source **C**linical **C**ontent **A**nalysis and **M**anagement **S**ystem


Goals
-----

  * Form versioning
  * Direct data entry instead of using paper forms
  * Data auditing
  * Singular data points with multiple references
  * Data workflow captured by the system design, but flexible enough to work for multiple use-cases
  * Secure, role-based data access control
  * A Relational Database that could describe how data are related through structure instead of convention


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
  > npm install -g less

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

  > cp src/occams/development-sample.ini etc/development.ini
  > cp src/occams/who-sample.ini etc/who.ini
  > vim etc/development.ini
  > vim etc/who.ini

Install the appropriate database tables::

  > createdb -U DBADMIN -O DBUSER DBNAME
  > os_initdb -c etc/development.ini


Start the web service::

  > gunicorn --reload --paste etc/development.ini


If you applications are using asynchronous tasks, you'll need to start the
celery worker::

  > celery worker --autoreload --app "occams.studies.tasks" --loglevel INFO --without-gossip --ini etc/development.ini
