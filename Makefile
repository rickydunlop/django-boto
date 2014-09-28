test:
	@coverage run tests.py
	@coverage report -m --include='django_boto*' --omit='*__init__*','*tests*'

req:
	@pip install -r requirements.txt

slow_test:
	@tox

default: req
