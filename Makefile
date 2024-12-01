# Define the Python interpreter
PYTHON := python

setup: requirements.txt
	pip install -r requirements.txt

build:
	docker pull infralightio/test-integration-api
	docker image tag infralightio/test-integration-api test/infralightio/test-integration-api:latest

test:
	pytest --html=report.html

test_faster:
	pytest pytest -n 4

