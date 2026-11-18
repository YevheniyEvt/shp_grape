# Quick commands for the shp_grape project. Run `just` to list them.

set dotenv-load
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

manage := "uv run manage.py"

# List available recipes
default:
    @just --list --unsorted

# Install all dependencies, git hooks, start the database and prepare it
setup:
    uv sync
    cd frontend; npm ci
    uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
    just up
    just migrate
    just compilemessages

# Start PostgreSQL in Docker
up:
    docker compose up -d --wait

# Stop Docker services
down:
    docker compose down

# Follow database logs
logs:
    docker compose logs -f db

# Run the Django development server
run:
    {{manage}} runserver

# Run the Next.js development server
front:
    cd frontend; npm run dev

# Apply database migrations and create the cache table
migrate:
    {{manage}} migrate
    {{manage}} createcachetable

# Create migrations (optionally for given apps)
makemigrations *args:
    {{manage}} makemigrations {{args}}

# Create a Django superuser
superuser:
    {{manage}} createsuperuser

# Load demo data (available from stage 3)
seed:
    {{manage}} seed_demo

# Reload demo data from scratch (available from stage 3)
seed-reset:
    {{manage}} seed_demo --reset

# Django shell
shell:
    {{manage}} shell

# PostgreSQL shell
dbshell:
    {{manage}} dbshell

# Run backend tests, e.g. `just test apps/core -k health`
test *args:
    uv run pytest {{args}}

# Backend tests with an HTML coverage report in htmlcov/
cov:
    uv run pytest --cov-report=html

# Run frontend unit tests
test-front:
    cd frontend; npm run test

# Lint and type-check backend and frontend
lint:
    uv run ruff check .
    uv run ruff format --check .
    cd frontend; npm run lint
    cd frontend; npm run typecheck
    cd frontend; npm run format:check

# Auto-format backend and frontend
fmt:
    uv run ruff check --fix .
    uv run ruff format .
    cd frontend; npm run format

# Extract translatable strings into .po files (backend + frontend)
messages:
    {{manage}} makemessages --all --ignore=.venv --ignore=frontend --ignore=node_modules --no-location
    {{manage}} makemessages_frontend

# Compile .po files into .mo files
compilemessages:
    {{manage}} compilemessages --ignore=.venv --ignore=frontend

# Generate TypeScript API types from the running backend's OpenAPI schema
gen-api:
    cd frontend; npm run gen:api

# Everything CI checks, locally
check:
    just lint
    {{manage}} makemessages_frontend --check
    just compilemessages
    just test
    just test-front

# Bump version, update CHANGELOG.md and create a git tag (see .context/02-versioning.md)
bump *args:
    uv run --frozen cz bump {{args}}

# Recreate the database from scratch and load demo data
[confirm("This deletes all local database data. Continue?")]
reset-db:
    docker compose down -v
    just up
    just migrate
    just seed
