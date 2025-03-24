import datetime

from pydantic import BaseModel


class DashboardEventDetailV1(BaseModel):
    total: int


class DashboardDataV1(BaseModel):
    last_updated: datetime.datetime
    downloads: DashboardEventDetailV1 | None
    installs: DashboardEventDetailV1 | None
    top_packages: dict[str, DashboardEventDetailV1 | None]
    top_commands: dict[str, DashboardEventDetailV1 | None]
