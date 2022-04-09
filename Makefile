fmt:
	find . -type f -name "*.py" | xargs black

# TODO: Recursive mypy file search.
# TODO: Mypy on unittest
test:
	python -m unittest discover -s src
	mypy src/*.py
