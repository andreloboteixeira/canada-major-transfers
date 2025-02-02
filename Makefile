.PHONY: install-deps run

# Create a conda environment with the name ary-strava-memory.
create-conda-env:
	conda create -n canada-major-transfers python=3.12

# Install all dependencies with poetry.
install-deps:
	poetry install

# Run the application (main.py inside the package ary_strava_memory under src).
run:
	poetry run python -m canada_major_transfers.main
