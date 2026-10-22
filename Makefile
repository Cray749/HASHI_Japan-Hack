# Plain targets. On Windows without make, run the commands by hand or use run.py.
PY ?= python

.PHONY: setup dev test lint bench build demo audio

setup:
	$(PY) -m pip install -r server/requirements.txt
	cd web && npm install

build:
	cd web && npm run build

dev: build
	$(PY) run.py

demo: build
	$(PY) run.py --demo

test:
	$(PY) -m pytest server/tests -q

lint:
	$(PY) -m ruff check server bench scripts run.py

bench:
	$(PY) -m bench.run

audio:
	$(PY) scripts/gen_audio.py
