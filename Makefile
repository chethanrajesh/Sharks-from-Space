# Small Makefile for Sharks-from-Space
.PHONY: setup fetch-data run-notebook run-app test clean

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

fetch-data:
	python get_sst.py
	python get_depth.py
	python get_data.py

run-notebook:
	jupyter lab notebooks/exploration.ipynb

run-app:
	streamlit run shark_app.py

test:
	python -m pytest

clean:
	rm -rf __pycache__ build dist *.egg-info
