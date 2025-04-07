# ruyi-backend

Server-side components of RuyiSDK.

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ruyisdk/ruyi-backend/ci.yml)
![GitHub License](https://img.shields.io/github/license/ruyisdk/ruyi-backend)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.12-blue)

## Config

It is preferred to configure `ruyi-backend` via environment variables,
as per cloud-native best practice. See [the example `.env` file](./example.env)
for supported config keys and respective defaults.

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
