SHELL := /bin/bash
PYTHON := python
PIP := pip

BUILD_DIR := .build
TOOLS_DIR := .tools
JAVASCRIPT_DIR := ./ripl/static/js

clean:
		find . -name "*.py[co]" -delete
			    rm -f .coverage

distclean: clean
		rm -rf $(BUILD_DIR)

run: deps
		dev_appserver.py .

test: clean integrations

deps: py_dev_deps py_deploy_deps js

py_deploy_deps: $(BUILD_DIR)/pip-deploy.log

py_dev_deps: $(BUILD_DIR)/pip-dev.log

$(BUILD_DIR)/pip-deploy.log: requirements.txt
		@mkdir -p .build
			$(PIP) install -Ur requirements.txt | tee $(BUILD_DIR)/pip-deploy.log
				$(PYTHON) $(TOOLS_DIR)/link_libs.py

$(BUILD_DIR)/pip-dev.log: requirements_dev.txt
		@mkdir -p .build
			$(PIP) install -Ur requirements_dev.txt | tee $(BUILD_DIR)/pip-dev.log

unit:
		nosetests

integrations:
		nosetests --logging-level=ERROR -a slow --with-coverage --cover-package=ripl

test: clean integrations

js:
		node $(JAVASCRIPT_DIR)/lib/r.js -o $(JAVASCRIPT_DIR)/buildconfig.js
