# --- Variables ---
# Define the name of the virtual environment directory
VENV_DIR = .venv

# Detect the operating system and set the Python executable path accordingly
# This allows the Makefile to work on both Windows and Unix-like systems (macOS, Linux)
ifeq ($(OS), Windows_NT)
	PYTHON = $(VENV_DIR)/Scripts/python
else
	PYTHON = $(VENV_DIR)/bin/python
endif

PYTHON_DIRS = src/ tests/


# .PHONY defines targets that are not associated with files
.PHONY: help install format lint test run

help:
	@echo "Usage:"
	@echo "  make setup      - Create a virtual environment and install all dependencies"
	@echo "  make install    - Install python dependencies"


# Setup the development environment by creating a venv and installing dependencies
setup:
	python -m venv $(VENV_DIR)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

# Install oython dependencies from requirements.txt
install:
	@$(PYTHON) -m pip install -r requirements.txt
