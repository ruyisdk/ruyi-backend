from fastapi import APIRouter

from ..db.conn import DIMainDB
from ..schema.frontend import DashboardDataV1, DashboardEventDetailV1

router = APIRouter()


@router.post("/fe/dashboard")
async def get_dashboard_data_v1(main_db: DIMainDB) -> DashboardDataV1:
    # TODO: query the crunched numbers
    _ = main_db

    # this is placeholder data
    top_pkgs = {
        "toolchain/gnu-milkv-milkv-duo-musl-bin": DashboardEventDetailV1(total=4),
        "toolchain/gnu-upstream": DashboardEventDetailV1(total=3),
        "toolchain/gnu-plct": DashboardEventDetailV1(total=2),
        "board-image/buildroot-sdk-milkv-duo": DashboardEventDetailV1(total=1),
    }
    top_cmds = {
        "riscv64-unknown-linux-musl-gcc": DashboardEventDetailV1(total=100),
        "riscv64-unknown-linux-musl-g++": DashboardEventDetailV1(total=50),
        "riscv64-unknown-linux-musl-ld": DashboardEventDetailV1(total=5),
    }
    return DashboardDataV1(
        downloads=DashboardEventDetailV1(total=20),
        installs=DashboardEventDetailV1(total=5),
        top_packages=top_pkgs,
        top_commands=top_cmds,
    )
