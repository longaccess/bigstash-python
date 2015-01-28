develop: setup-git
	pip install peep
	peep install -r requirements/test.txt
	pip install --no-deps -e .

setup-git:
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../hooks/* ./

lint-python:
	@echo "Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8
	@echo ""

test:
	@echo "Running nosetests -sv"
	nosetests -sv
	@echo ""
