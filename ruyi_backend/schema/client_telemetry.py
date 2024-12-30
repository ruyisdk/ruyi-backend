from typing import NotRequired, TypeAlias, TypedDict

## Start of copied code from ruyisdk/ruyi
## This should stay mostly in sync with the client code


class NodeInfo(TypedDict):
    v: int
    report_uuid: str

    arch: str
    ci: str
    libc_name: str
    libc_ver: str
    os: str
    os_release_id: str
    os_release_version_id: str
    shell: str

    riscv_machine: NotRequired["RISCVMachineInfo"]


class RISCVMachineInfo(TypedDict):
    model_name: str
    cpu_count: int
    isa: str
    uarch: str
    uarch_csr: str
    mmu: str


class AggregatedTelemetryEvent(TypedDict):
    time_bucket: str
    kind: str
    params: list[
        tuple[str, str] | list[str]
    ]  # tuple[str, str] round-trips back to list[str]
    count: int


class UploadPayload(TypedDict):
    fmt: int
    nonce: str
    ruyi_version: str
    installation: NotRequired[NodeInfo | None]
    events: list[AggregatedTelemetryEvent]


AggregateKey: TypeAlias = tuple[tuple[str, str], ...]

## End of copied code from ruyisdk/ruyi
