# Convenience targets for {{project_name}}.
# Every target assumes the project virtualenv is already active.

.PHONY: help run migrations migrate check test shell superuser static lint verify

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

run:  ## Start the development server on 0.0.0.0:8000
	python manage.py runserver 0.0.0.0:8000

migrations:  ## Create migrations for the api app
	python manage.py makemigrations api

migrate:  ## Apply migrations
	python manage.py migrate

check:  ## Run Django system checks
	python manage.py check

test:  ## Run the test suite
	pytest

shell:  ## Open the Django shell
	python manage.py shell

superuser:  ## Create a superuser
	python manage.py createsuperuser

static:  ## Collect static files
	python manage.py collectstatic --noinput

verify:  ## Full pre-commit gate: checks, missing migrations, tests
	python manage.py check
	python manage.py makemigrations --check --dry-run
	pytest
