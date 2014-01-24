occams.clinical README
==================

Requirements
---------------
python 2.6+
# asynchrounous processes
rabbitmq-server
# message broker
redis


Getting Started
---------------

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- $venv/bin/initialize_occams.clinical_db development.ini

- $venv/bin/pserve development.ini


Using gUnicorn (for development)
--------------------------------

watchmedo auto-restart -i "*/alembic/*;*/tests/*" -p "*.py;*.ini;*.yml" -d ./src -R -- gunicorn --paste etc/clinical.ini

watchmedo auto-restart -i "*/alembic/*;*/tests/*" -p "*.py;*.ini" -R -d ./src -- celery -A "occams.clinical.tasks" worker -l info --ini etc/clinical.ini

