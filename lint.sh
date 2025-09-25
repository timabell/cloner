#!/bin/bash -v
set -e
black --line-length=88 **/*.py
isort --profile=black **/*.py
# C0114=missing-module-docstring, C0116=missing-function-docstring, R0903=too-few-public-methods
pylint --disable=C0114,C0116,R0903 --max-line-length=88 **/*.py
