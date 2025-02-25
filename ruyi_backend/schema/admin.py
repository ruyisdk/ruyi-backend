import datetime

from pydantic import BaseModel, Field


class ReqProcessTelemetry(BaseModel):
    """Request schema for the ``/admin/process-telemetry-v1`` endpoint."""

    time_start: datetime.datetime = Field(
        # 00:00:00 yesterday
        default_factory=lambda: datetime.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        + datetime.timedelta(days=-1),
        description="The start of the time range to process telemetry data for, inclusive.",
        examples=["2021-01-01T00:00:00+08:00"],
    )

    time_end: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The end of the time range to process telemetry data for, exclusive.",
        examples=["2021-01-02T00:00:00+08:00"],
    )
