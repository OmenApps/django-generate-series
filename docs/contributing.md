# Contributing

We welcome contributions that meet the goals and standards of this project. Contributions may include bug fixes, feature development, corrections or additional context for the documentation, submission of Issues on GitHub, etc.

For development and testing, you can run your own instance of Postgres (either locally or using a DBaaS), or you can use the provided Docker Compose yaml file to provision a containerized instance and data volume locally.


## Getting up-and-running

### Using Your Own postgres Instance

To develop using your own Postgres instance, you may set the following environmental variables on your machine:

- DB_NAME (defaults to "postgres")
- DB_NAME_WITH_EXTENSIONS (defaults to "postgres_with_extensions")
- DB_USER (defaults to "docker")
- DB_PASSWORD (defaults to "docker")
- DB_HOST (defaults to "localhost")
- DB_PORT (defaults to "9932")

The process of setting environmental variables varies between different operating systems. Generally, on macOS and Linux, you can use the following convention in the console:

```bash
export KEY=value
```

### Using the Provided Docker Compose Postgres Instance

This guide assumes you already have [Docker and Docker Compose installed](https://docs.docker.com/compose/install/).

#### Build & Bring up the Docker Compose container for Postgres services:

Run the following command to build and bring up the postgres service.

```bash
docker-compose -f dev.yml up -d --no-deps --force-recreate --build postgres
```

These are the database connection details:

    DB = postgres *and* postgres_with_extensions
    USER = docker
    PASSWORD = docker
    HOST = postgres
    PORT = 9932

Note that the docker-compose postgres service creates two databases:

- The default `postgres` database with default functionality. In Django tests, this is the `default` database.
- A database named `postgres_with_extensions`, which has the plpython3u extension installed. In Django tests, this is the `with_extensions` database.

*(The PL/Python procedural language is used in tests of advanced backend functionality which can make use of python-based graph libraries)*

#### To check the status of the database container:

```bash
docker ps
```

Once running, you should be able to connect using the test app, psql, or other Postgres management tools if desired.

#### To completely remove the container and associated data:

```bash
docker-compose -f dev.yml down --rmi all --remove-orphans -v
```

### Once you have a Running Postgres Instance

#### Create a Python virtual environment:

```bash
python3 -m venv venv
```

#### Activate the virtual environment for local development:

```bash
source venv/bin/activate
```

#### Install packages for development and testing:

This installs all packages needed for development and testing, and installs django-generate-series in editable mode from the local repo.

```bash
pip install -r ./tests/requirements.txt
```

#### Install pre-commits:

These ensure code is formatted correctly upon commit. See [the pre-commit docs](https://pre-commit.com/) for more information.

```bash
pre-commit install
```

#### Run the tests:

```bash
pytest
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


## Package Structure

Because django-generate-series supports multiple types of directed graphs, the underlying functionality can be a bit complex to understand at first. This shouldn't matter much if you are only building, querying, or manipulating graphs.

If you want to contribute to development of this package or extend the functionality of django-generate-series by creating installable apps and plugins for new graph types or customized graph behavior, it is critical to understand what functionality exists where.

| Folder/File                        |                                                                              |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| 📦django_generate_series            |                                                                              |
| ┣ 📂models                          |                                                                              |
| ┃ ┣ 📜__init__.py                   |                                                                              |
| ┃ ┣ 📜abstract_base_models.py       | Lowest-level models (used for validating model type inheritance)             |
| ┃ ┣ 📜abstract_base_graph_models.py | Provides functionality common to all graphs                                  |
| ┃ ┣ 📜abstract_graph_models.py      | Breaks out functionality specific to each graph type                         |
| ┃ ┗ 📜model_factory.py              | Provides the means of creating multiple graph moseld for each graph type     |
| ┣ 📂static                          | Package Static files                                                         |
| ┣ 📂templates                       | Package Default Templates                                                    |
| ┣ 📂templatetags                    | Package Templatetags                                                         |
| ┣ 📜__init__.py                     |                                                                              |
| ┣ 📜admin.py                        | Tools for working with graphs in Django admin                                |
| ┣ 📜apps.py                         |                                                                              |
| ┣ 📜context_managers.py             | Utility context manager to simplify reference to a particular graph instance |
| ┣ 📜exceptions.py                   | Exceptions specific to this package                                          |
| ┣ 📜fields.py                       | CurrentGraphField which simplifies working with Edge and Node models         |
| ┣ 📜manager_methods.py              | WIP                                                                          |
| ┣ 📜model_methods.py                | WIP                                                                          |
| ┣ 📜query_utils.py                  | Uilities for building and manipulating queries                               |
| ┣ 📜queryset_methods.py             | WIP                                                                          |
| ┣ 📜urls.py                         |                                                                              |
| ┣ 📜validators.py                   | WIP                                                                          |
| ┗ 📜views.py                        |                                                                              |


## Build the docs

Within the docs directory, run this from the console:

```bash
make html
```