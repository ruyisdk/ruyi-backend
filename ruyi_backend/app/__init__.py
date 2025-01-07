from .root import app as app

# register the various API endpoints
from . import frontend as frontend
from . import misc as misc
from . import telemetry as telemetry

app.include_router(frontend.router)
app.include_router(misc.router)
app.include_router(telemetry.router)
