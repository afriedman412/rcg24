REPO = rcg
VENV_NAME = venv
VENV_PATH = $(VENV_NAME)/bin/activate
PYTHON := $(VENV_NAME)/bin/python

.PHONY: venv

venv:
ifeq ($(OS),Windows_NT)
	python -m venv $(VENV_NAME)
	. $(VENV_PATH) && pip install -r requirements.txt
else
	python3 -m venv $(VENV_NAME)
	. $(VENV_PATH); pip install -r requirements.txt
endif

activate:
	. source $(VENV_PATH)

.PHONY: test

test:
	python -m pytest tests/ -vv

.PHONY: install

install: venv
	. $(VENV_PATH); pip install --upgrade -r requirements.txt

.PHONY: install-dev

install-dev: venv
	. $(VENV_PATH); pip install --upgrade -r requirements-dev.txt

.PHONY: update

update: venv
	. $(VENV_PATH); pip install --upgrade -r requirements.txt

.PHONY: clean

clean:
	rm -rf $(VENV_NAME)

.PHONY: dev-reqs

dev-reqs:
	. $(VENV_PATH); pip install autopep8 isort mypy flake8 pytest

check-autopep:
	${PYTHON} -m autopep-8 -i $(REPO)/*.py tests/*.py

check-isort:
	${PYTHON} -m isort --check-only $(REPO) tests

check-flake:
	${PYTHON} -m flake8 $(REPO) tests

check-mypy:
	${PYTHON} -m mypy --strict --implicit-reexport $(REPO)

lint: check-flake check-mypy check-autopep check-isort

format:
	${PYTHON} -m autopep8 -i $(REPO)/*.py tests/*.py $(REPO)/src/*.py 
	${PYTHON} -m isort $(REPO) tests