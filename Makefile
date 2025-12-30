.PHONY: venv install run clean

venv:
	@test -d .venv || python -m venv .venv

install: venv
	.venv/bin/python -m pip install -r requirements.txt

run:
	.venv/bin/python main.py

run-debug:
	.venv/bin/python main.py --debug 

clean:
	./scripts/cleanup_pycache.sh
