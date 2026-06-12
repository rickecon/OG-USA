# GNU Makefile that documents and automates common development operations
#              using the GNU make tool (version >= 3.81)
# Development is typically conducted on Linux or Max OS X (with the Xcode
#              command-line tools installed), so this Makefile is designed
#              to work in that environment (and not on Windows).
# USAGE: OG-USA$ make [TARGET]

.PHONY=help
help:
	@echo "USAGE: make [TARGET]"
	@echo "TARGETS:"
	@echo "help       : show help message"
	@echo "clean      : remove .pyc files and local ogusa package"
	@echo "install    : build and install local package"
	@echo "test       : run tests with coverage"
	@echo "pytest     : generate report for and cleanup after"
	@echo "             pytest -W ignore -m ''"
	@echo "lint       : check code using ruff"
	@echo "coverage   : generate test coverage report"
	@echo "git-sync   : synchronize local, origin, and upstream Git repos"
	@echo "git-pr N=n : create local pr-n branch containing upstream PR"
	@echo "pip-package: build package for distribution"
	@echo "format     : format code using ruff"
	@echo "documentation : build documentation using jupyter-book"
	@echo "new-baseline : update baseline parameters and save to json file"


.PHONY=clean
clean:
	@find . -name *pyc -exec rm {} \;
	@find . -name *cache -maxdepth 1 -exec rm -r {} \;

install:
	uv sync --extra dev

test:
	uv run pytest -m 'not local' --cov=./ --cov-report=xml

.PHONY=pytest
pytest:
	@uv run pytest -W ignore

.PHONY=lint
lint:
	uv run ruff check --force-exclude .

define coverage-cleanup
rm -f .coverage htmlcov/*
endef

COVMARK = ""

OS := $(shell uname -s)

.PHONY=coverage
coverage:
	@$(coverage-cleanup)
	@uv run coverage run -m pytest -v -m $(COVMARK) > /dev/null
	@uv run coverage html --ignore-errors
ifeq ($(OS), Darwin) # on Mac OS X
	@open htmlcov/index.html
else
	@echo "Open htmlcov/index.html in browser to view report"
endif
	@$(pytest-cleanup)

.PHONY=git-sync
git-sync:
	@./gitsync

.PHONY=git-pr
git-pr:
	@./gitpr $(N)

pip-package:
	uv build

format:
	uv run ruff format --force-exclude .

documentation:
	uv run jupyter-book clean docs/book
	uv run python docs/create_doc_figures.py
	uv run jupyter-book build docs/book

new-baseline:
	uv run python ogusa/update_baseline.py
