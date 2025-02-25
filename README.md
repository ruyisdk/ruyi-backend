# ruyi-backend

Server-side components of RuyiSDK

## Config

It is preferred to configure `ruyi-backend` via environment variables,
as per cloud-native best practice. Below are the supported config keys
and respective defaults:

```sh
#
# Global options
#

# Debugging flag
RUYI_BACKEND_DEBUG=true

#
# Main database connection
#

# SQLAlchemy DSN
RUYI_BACKEND_DB_MAIN__DSN=""
# Database name for ruyi-backend
RUYI_BACKEND_DB_MAIN__NAME=ruyisdk

# In-house server-side analytics Elasticsearch host
RUYI_BACKEND_ES_MAIN__HOST="https://foo.example.com/bar/"
# Authentication parameters
RUYI_BACKEND_ES_MAIN__BASIC_AUTH="user:pass"
```

Variable names are case-insensitive.

## Debugging

To run the project locally, you have to set up a virtual environment and install the runtime dependencies.

```sh
python -m venv ./.venv
. ./.venv/bin/activate

poetry install  # in case poetry >= 2.0 is already available
```

Then just invoke `fastapi` at the project root:

```sh
fastapi run ruyi_backend
```

For optional access to the online staging environment, you may have to set up
some kind of proxy and/or port forwarding. This is out of scope of this document.

There are also some convenience facilities provided for easier debugging:

* `scripts/ruyi-backend-mysql-main`: equivalent to `mariadb` or `mysql` (in that order) with the DSN configured in the environment.
