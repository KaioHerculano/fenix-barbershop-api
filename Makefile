PYTHON = python
MANAGE = $(PYTHON) manage.py
MIN_COVERAGE = 90

.PHONY: help install safety run migrate migrations shell loaddata format lint test test-app test-coverage pre-commit check-migrations ci-check clean

help:
	@echo "Comandos disponíveis:"
	@echo "  install        - Instala as dependências via poetry"
	@echo "  run            - Inicia o servidor"
	@echo "  migrate        - Aplica as migrações"
	@echo "  migrations     - Cria migrações (uso: make migrations APP=nome)"
	@echo "  shell          - Abre o shell do Django"
	@echo "  format         - Roda black e isort"
	@echo "  lint           - Roda ruff"
	@echo "  test           - Roda todos os testes"
	@echo "  test-coverage  - Relatório de cobertura"
	@echo "  clean          - Limpa cache e arquivos .pyc"

install:
	poetry install

safety:
	safety check -r requirements.txt --full-report

run:
	$(MANAGE) runserver

migrate:
	$(MANAGE) migrate

migrations:
	$(MANAGE) makemigrations $(APP)

shell:
	$(MANAGE) shell_plus

loaddata:
	$(MANAGE) loaddata $(FIXTURE)

format:
	black .
	isort .

lint:
	ruff check .

test:
	$(MANAGE) test -v 2

test-app:
	$(MANAGE) test $(APP) -v 2

test-coverage:
	poetry run coverage erase
	poetry run coverage run manage.py test -v 2
	poetry run coverage report -m --fail-under=$(MIN_COVERAGE)
	poetry run coverage html

pre-commit:
	pre-commit run --all-files

check-migrations:
	$(MANAGE) makemigrations --check --no-input

ci-check: safety lint check-migrations test-coverage

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
