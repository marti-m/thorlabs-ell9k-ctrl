# Thorlabs ELL9K RC

Server for controlling the Thorlabs ELL9K filter slider


## Requirements

 - Python 3.6+
 - [poetry](https://python-poetry.org/)


## Makefile targets:

- `prepare`: install the required dependencies using poetry. On Windows, run `poetry install`.
- `run`: run the plugin. On Windows, `poetry run python -m ELL9K.main`.
- `clean`: removes poetry lockfile and virtual environment.
- `services` (Unix only): create and install a unit service file to runs the plugin server via `systemctl`.
