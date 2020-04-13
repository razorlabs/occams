
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


Features
--------

* Configurable forms with version tagging
* Study visit matrix configuration
* Direct data entry instead of using paper forms
* Data export tools
* Immutable data auditing
* Data workflow captured by the system design, but flexible enough to work for multiple use-cases
* Secure, role-based data access control


System Requirements
-------------------

* Python 3.7+
* npm 10
    - bower
    - lessc (must be installed globally, i.e. with "-g" option)
* redis
* PostgreSQL 9.6+


Development
-----------

This application uses Docker_ to setup a *development environment* with dummy
user accounts. It is recommended you familiarize yourself with some basic
knowledge of how it works.

.. _Docker: https://www.docker.com/

- macOS: https://docs.docker.com/docker-for-mac/
- Windows: https://docs.docker.com/docker-for-windows/
- Linux:  https://docs.docker.com/engine/installation/linux/

Installation
++++++++++++

#. Clone the application and build the containers::

      > git clone https://github.com/razorlabs/occams
      > cd occams
      > docker-compose build

   This will take a moment, so it's a good idea to refill on coffee at this time.

#. Back? Ok, spin up the containers, there will some additional building for
   dependencies, this is normal::

      > docker-compose up -d

#. Navigate to http://localhost:3000/


You now should have a working OCCAMS instance.


Common Tasks
""""""""""""

How do I add more users?
''''''''''''''''''''''''

Modify the data setting in the `[plugin:dev_users]` section of the develop.ini
file. There is already a test user there for you, so use that a template.


How do I run the tests?
'''''''''''''''''''''''

Create a test user and database to run the tests.

::

    > docker-compose run --rm app pytest --db "postgresql://test:test@postgres-test/test" --redis redis://redis/9

How do I check the logs?
''''''''''''''''''''''''

::

    > docker-compose logs -f

How do I access the database?
'''''''''''''''''''''''''''''

Install the Postgres client on the host machine and run::

  > psql -U occams -h localhost

How do I restart the application?
'''''''''''''''''''''''''''''''''

::

    > docker-compose restart app


How do I reset the database and start over again?
'''''''''''''''''''''''''''''''''''''''''''''''''

::

    > docker-compose down
    > docker volume rm postgres
    > docker-compose up -d
    > docker-compose run app occams_initdb develop.ini
