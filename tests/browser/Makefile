REPORTER = dot
PORT = 8080

install:
	npm install .

test:
	@./node_modules/.bin/mocha \
			--require ./test/common \
			--reporter $(REPORTER) \
			--growl \
			./test/

test-web:
	@./node_modules/.bin/serve -p $(PORT) .

.PHONY: test
