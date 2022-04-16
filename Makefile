fmt:
	find . -type f -name "*.py" | xargs black

test:
	python -m unittest discover -s src/tests
	mypy src/*.py
	mypy src/*/*.py
