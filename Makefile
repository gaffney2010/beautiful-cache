fmt:
	find . -type f -name "*.py" | xargs black

test:
	python -m unittest discover -s src
