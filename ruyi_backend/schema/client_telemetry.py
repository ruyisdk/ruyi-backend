from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt


## Start of adapted code from ruyisdk/ruyi
## This should stay mostly in sync with the client code


class NodeInfo(BaseModel):
    v: PositiveInt
    report_uuid: UUID

    arch: str
    ci: str
    libc_name: str
    libc_ver: str
    os: str
    os_release_id: str
    os_release_version_id: str
    shell: str

    riscv_machine: "RISCVMachineInfo | None" = Field(default=None)


class RISCVMachineInfo(BaseModel):
    model_name: str
    cpu_count: int
    isa: str
    uarch: str
    uarch_csr: str
    mmu: str


class AggregatedTelemetryEvent(BaseModel):
    time_bucket: str
    kind: str
    params: list[tuple[str, str]]
    count: int


class UploadPayload(BaseModel):
    fmt: PositiveInt
    nonce: str
    ruyi_version: str

    report_uuid: UUID | None = Field(default=None)
    """Optional field in case the client wishes to report this, and nothing
    else. If `installation` is present, this field is ignored."""

    installation: NodeInfo | None = Field(default=None)
    """More detailed installation info that the client has user consent to report."""

    events: list[AggregatedTelemetryEvent] = Field(default=[])
    """Aggregated telemetry events that the client has user consent to upload."""


AggregateKey: TypeAlias = tuple[tuple[str, str], ...]

## End of copied code from ruyisdk/ruyi
