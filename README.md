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
```

Variable names are case-insensitive.
