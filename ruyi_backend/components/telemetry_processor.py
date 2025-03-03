import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from ..db.schema import (
    ModelTelemetryAggregatedEvent,
    ModelTelemetryInstallationInfo,
    ModelTelemetryRISCVMachineInfo,
    telemetry_aggregated_events,
    telemetry_installation_infos,
    telemetry_riscv_machine_infos,
)
from ..schema.client_telemetry import (
    UploadPayload,
)


async def process_telemetry_data(
    conn: AsyncConnection,
    raw_events: list[UploadPayload],
) -> None:
    """
    Processes raw telemetry events, aggregates them, and stores them in the database.
    """

    # Buffers for batch insertion
    aggregated_events_buffer: list[ModelTelemetryAggregatedEvent] = []
    installation_infos_buffer: dict[uuid.UUID, ModelTelemetryInstallationInfo] = {}
    riscv_machine_infos_buffer: list[ModelTelemetryRISCVMachineInfo] = []

    for event in raw_events:
        # Process aggregated events
        for agg_event in event.events:
            aggregated_events_buffer.append(
                ModelTelemetryAggregatedEvent(
                    time_bucket=agg_event.time_bucket,
                    kind=agg_event.kind,
                    params_kv_raw=agg_event.params,
                    count=agg_event.count,
                )
            )

        # Process installation info (assuming one per upload)
        installation_info = event.installation
        if installation_info:
            installation_infos_buffer[installation_info.report_uuid] = (
                ModelTelemetryInstallationInfo(
                    report_uuid=installation_info.report_uuid,
                    arch=installation_info.arch,
                    ci=installation_info.ci,
                    libc_name=installation_info.libc_name,
                    libc_ver=installation_info.libc_ver,
                    os=installation_info.os,
                    os_release_id=installation_info.os_release_id,
                    os_release_version_id=installation_info.os_release_version_id,
                    shell=installation_info.shell,
                )
            )

            if riscv_machine_info := installation_info.riscv_machine:
                riscv_machine_infos_buffer.append(
                    ModelTelemetryRISCVMachineInfo(
                        model_name=riscv_machine_info.model_name,
                        cpu_count=riscv_machine_info.cpu_count,
                        isa=riscv_machine_info.isa,
                        uarch=riscv_machine_info.uarch,
                        uarch_csr=riscv_machine_info.uarch_csr,
                        mmu=riscv_machine_info.mmu,
                    )
                )

    # Batch insert
    if aggregated_events_buffer:
        await conn.execute(
            insert(telemetry_aggregated_events).values(aggregated_events_buffer)
        )

    if installation_infos_buffer:
        await conn.execute(
            insert(telemetry_installation_infos).values(
                list(installation_infos_buffer.values())
            )
        )

    if riscv_machine_infos_buffer:
        await conn.execute(
            insert(telemetry_riscv_machine_infos).values(riscv_machine_infos_buffer)
        )
