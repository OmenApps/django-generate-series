# Contributing

We welcome contributions that meet the goals and standards of this project. Contributions may include bug fixes, feature development, corrections or additional context for the documentation, submission of Issues on GitHub, etc.

For development and testing, you can run your own instance of Postgres (either locally or using a DBaaS), or you can use the provided Docker Compose yaml file to provision a containerized PostgreSQL instance locally.


## Getting up-and-running

### Clone the Repository

```bash
git clone https://github.com/OmenApps/django-generate-series.git
cd django-generate-series
```

### Install uv

If you don't already have [uv](https://docs.astral.sh/uv/) installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies

```bash
uv sync --extra dev --prerelease=allow
```

### Using your own postgres instance

To develop using your own Postgres instance, you may set the following environmental variables on your machine:

- DB_NAME (defaults to "postgres")
- DB_USER (defaults to "docker")
- DB_PASSWORD (defaults to "docker")
- DB_HOST (defaults to "localhost")
- DB_PORT (defaults to "9932")

The process of setting environmental variables varies between different operating systems. Generally, on macOS and Linux, you can use the following convention in the console:

```bash
export KEY=value
```

### Using the provided docker compose postgres instance

This guide assumes you already have [Docker and Docker Compose installed](https://docs.docker.com/compose/install/).

#### Start the PostgreSQL service:

```bash
docker compose up -d
```

These are the database connection details:

    DB = postgres
    USER = docker
    PASSWORD = docker
    HOST = localhost
    PORT = 9932

#### To view logs of the database container:

```bash
docker compose logs postgres
```

Once running, you should be able to connect using the test app, psql, or other Postgres management tools if desired.

#### To completely remove the container and associated data:

```bash
docker compose down --rmi all --remove-orphans -v
```

### Once you have a Running Postgres Instance you can:


#### Install pre-commits:

These ensure code is formatted correctly upon commit. See [the pre-commit docs](https://pre-commit.com/) for more information.

```bash
uv run pre-commit install
```

#### Run the tests:

```bash
uv run pytest
```

#### Run the full test matrix via nox:

```bash
uv run nox --session=tests
```

#### Run code coverage report:

```bash
uv run nox --session=coverage
```

#### Run linting:

```bash
uv run nox --session=pre-commit
```

#### Check the django test project:

```bash
uv run python manage.py check
```

#### To run the example project in the python REPL:

```bash
uv run python manage.py shell_plus
```

## Build the docs

```bash
uv run nox --session=docs-build
```
