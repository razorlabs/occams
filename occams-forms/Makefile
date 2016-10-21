test-unit:
	$(VIRTUAL_ENV)/bin/nosetests -e function -e browser ./tests

test-functional:
	$(VIRTUAL_ENV)/bin/nosetests -e unit -e browser ./tests

test-browser:
	make -C ./tests/browser test

test-browser-web:
	make -C ./tests/browser test-web

test-all:
	$(VIRTUAL_ENV)/bin/nosetests ./tests && make -C ./tests/browser test

serve:
	$(VIRTUAL_ENV)/bin/watchmedo auto-restart \
		--ignore-pattern "*/alembic/*;*/tests/*" \
		--pattern "*.py;*.ini" \
		--directory $(VIRTUAL_ENV)/src \
		--recursive \
		-- \
		$(VIRTUAL_ENV)/bin/gunicorn \
		--error-logfile - \
		--log-config $(VIRTUAL_ENV)/etc/development.ini \
		--timeout 100000 \
		--paste $(VIRTUAL_ENV)/etc/development.ini


celeryd:
