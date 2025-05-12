from .root import app as app

# register the various API endpoints
from . import admin as admin
from . import frontend as frontend
from . import misc as misc
from . import news as news
from . import releases as releases
from . import telemetry as telemetry

app.include_router(admin.router)
app.include_router(frontend.router)
app.include_router(misc.router)
app.include_router(news.router)
app.include_router(releases.router)
app.include_router(telemetry.router)
