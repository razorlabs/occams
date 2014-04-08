occams.clinical
===============

Clinical trials data management software.

System Requirements
-------------------

* Python 2.7+
* redis
* PostgreSQL 9.3+


Extra Python Requirements
-------------------------

These dependencies are not listed in the `setup.py` because
ideally you should be able to use any gevent-enabled WSGI server.

* gUnicorn
* watchdog

Getting Started
---------------

::

  cd $venv

  # Optional put these in a requirements.txt...
  pip install -e <path/to/occams.datastore>
  pip install -e <path/to/occams.roster>
  pip install -e <path/to/occams.form>
  pip install -e <path/to/occams.lab>
  pip install -e <path/to/occams.clniical>

  # If you're starting with a fresh installation
  $venv/bin/oc_initdb <YOURINI>


Serving with gUnicorn (for development)
+++++++++++++++++++++++++++++++++++++++

::

  watchmedo auto-restart \
            --ignore-pattern "*/alembic/*;*/tests/*" \
            --pattern "*.py;*.ini" \
            --directory ./src \
            --recursive \
            -- \
            gunicorn --paste <YOURINI>

::

  watchmedo auto-restart \
            --ignore-pattern "*/alembic/*;*/tests/*" \
            --pattern "*.py;*.ini" \
            --directory ./src \
            --recursive \
            -- \
            celery worker \
            --app "occams.clinical.tasks" \
            --loglevel INFO \
            --without-gossip \
            --ini <YOURINI>


Serving with gUnicorn (for production)
++++++++++++++++++++++++++++++++++++++

::

  gunicorn --paste <YOURINI>


::

  celery worker \
           --app "occams.clinical.tasks" \
           --without-gossip \
           --loglevel INFO \
           --init <YOURINI>
