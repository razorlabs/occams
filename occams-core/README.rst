
::

    .d88888b.   .d8888b.   .d8888b.        d8888 888b     d888  .d8888b.
   d88P" "Y88b d88P  Y88b d88P  Y88b      d88888 8888b   d8888 d88P  Y88b
   888     888 888    888 888    888     d88P888 88888b.d88888 Y88b.
   888     888 888        888           d88P 888 888Y88888P888  "Y888b.
   888     888 888        888          d88P  888 888 Y888P 888     "Y88b.
   888     888 888    888 888    888  d88P   888 888  Y8P  888       "888
   Y88b. .d88P Y88b  d88P Y88b  d88P d8888888888 888   "   888 Y88b  d88P
    "Y88888P"   "Y8888P"   "Y8888P" d88P     888 888       888  "Y8888P"


**O**\ pen Source **C**\ linical **C**\ ontent **A**\ nalysis and **M**\ anagement **S**\ ystem


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

  $ npm install -g bower
  $ npm install -g less

Create a virtual environment for your work::

  $ virtualenv MYPROJECT
  $ source MYPROJECT/bin/activate

Next, create the necesary directories::

  $ cd MYPROJECT
  $ mkdir -p  etc  var/exports  var/blobs  src

You'll need to git checkout the web application. If you are
using your own forks, change ``younglabs`` to yours. The reason we
checkout each project individually is because pip will replace all
git changes/history the next time your run pip install on a git
repo, which can lead you to lose a lot of work and sanity::

  $ cd src
  $ git clone git@github.com:YOURID/occams

If you plan on working on add-ons, it is recommended you install the
following as well::

  $ git clone git@github.com:YOURID/occams_datastore
  $ git clone git@github.com:YOURID/occams_forms
  $ git clone git@github.com:YOURID/occams_accounts
  $ git clone git@github.com:YOURID/occams_roster
  $ git clone git@github.com:YOURID/occams_studies
  $ git clone git@github.com:YOURID/occams_lims


Now that your projects are checked out, copy and update the ``requirements.txt``
found in the ``occams`` project directory.::

  $ cd $VIRTUAL_ENV
  $ cp src/occams/requirements.txt .
  $ vim requirements.txt
  $ pip install -U -r requirements.txt

Once everything is installed you'll need to configure the application with
your desired development environment settings::

  $ cp src/occams/sample.ini etc/development.ini
  $ vim etc/development.ini

Install the appropriate database tables::

  $ createdb -U DBADMIN -O DBUSER DBNAME
  $ occams_initdb etc/development.ini


Start the web service::

  $ gunicorn --reload --paste etc/development.ini


If you applications are using asynchronous tasks, you'll need to start the
celery worker::

  $ celery worker --autoreload --app occams --loglevel INFO --without-gossip --ini etc/development.ini


Creating your own app
---------------------

**TODO**

Database Migrations
+++++++++++++++++++

If your app depends on OCCAMS's database structure, it is advised you use `alembic branchpoints`__
with a dedicated label for your project.

.. _alembic: https://alembic.readthedocs.org/en/latest/branches.html#working-with-multiple-bases

__ alembic_

Use ``alembic history`` to inspect the current history of OCCAMS application database structures.
Ideally, your project should follow it's only independent history,
were you might depend on certain dependant database structure changes. If this is the case, please
refer to the following scenarios:

New Projects
''''''''''''

If your project **begins as an independent** database structure::

  $ alembic -c /path/to/ini revision -m "MESSAGE" --head=base --branch-label=MYAPP --version-path=/path/to/app/versions


If your project **begins depending** on a specific database structure::

  $ alembic -c /path/to/ini revision -m "MESSAGE" --head=REVISION --splice --branch-label=MYAPP --version-path=/path/to/app/versions

Existing Projects
'''''''''''''''''

If your project's revision **continues** the history::

  $ alembic -c /path/to/ini revision -m "MESSAGE" --head=MYAPP@head --version-path=/path/to/app/versions

If your project's revision depends on a **another** project's revision::

  $ alembic -c /path/to/ini revision -m "MESSAGE" --head=MYAPP@base --depends-on=REVISION --version-path=/path/to/app/versions
  

