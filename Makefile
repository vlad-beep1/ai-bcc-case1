VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
EXPORT := PYTHONPATH=.

all: run

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

analyze:
	$(EXPORT) $(PYTHON) -m src.runner

run: analyze
	$(EXPORT) streamlit run src/demo_app.py

clean:
	rm -rf $(VENV) submission.csv submission/ __pycache__ .streamlit
