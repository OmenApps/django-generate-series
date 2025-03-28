# Contributing

We welcome contributions that meet the goals and standards of this project. Contributions may include bug fixes, feature development, corrections or additional context for the documentation, submission of Issues on GitHub, etc.

For development and testing, you can run your own instance of Postgres (either locally or using a DBaaS), or you can use the provided Docker Compose yaml file to provision a containerized instance and data volume locally.


## Getting up-and-running

### Clone the Repository

```bash
git clone https://github.com/OmenApps/django-generate-series.git
```

### Create a Virtual Environment

```bash
python3 -m venv .venv
```

### Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Install Poetry if you haven't already

```bash
pip install --upgrade poetry
```

### Install requirements with Poetry

Install all packages needed for development and testing.

```bash
poetry install --with dev
```

*Note: You may need to run `poetry update` if there have been minor version updates to required packages.*

#### Start poetry environment in shell

```bash
poetry shell
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

#### Build & Bring up the Docker Compose container for Postgres services:

Run the following command to build and bring up the postgres service.

```bash
docker compose up -d --no-deps --force-recreate --build
```

These are the database connection details:

    DB = postgres
    USER = docker
    PASSWORD = docker
    HOST = postgres
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
pre-commit install
```

#### Run the tests:

```bash
python -m pytest
```

#### Run code coverage report:

```bash
coverage run -m pytest
```

#### Create html coverage report:

```bash
coverage html
```

#### Check the django test project:

```bash
python manage.py check
```

#### To run the example project in the python REPL:

```bash
python manage.py shell_plus
```

## Build the docs

Within the docs directory, run this from the console:

```bash
make html
```
