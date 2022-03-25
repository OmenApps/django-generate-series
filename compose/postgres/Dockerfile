FROM postgres:14

# Install plpython3 extension
RUN apt-get update && apt-get -y install git build-essential postgresql-contrib postgresql-plpython3-14 -y

# Copy over the sql file which runs CREATE EXTENSION
COPY ./compose/postgres/extensions.sql /docker-entrypoint-initdb.d/
