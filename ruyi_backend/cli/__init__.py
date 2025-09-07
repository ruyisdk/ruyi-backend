"""
CLI management tool for the ruyi-backend package.
"""

import argparse
import asyncio
import logging
import sys
from typing import Callable, NoReturn

from ..config import get_env_config, init
from .cmd_password import do_hash_password, do_test_password
from .cmd_sync_releases import do_sync_releases


def main(argv: list[str]) -> int:
    """Real entrypoint of ruyi-backend, allowing to customize argv."""

    init()
    cfg = get_env_config()

    logging.basicConfig(
        level=logging.DEBUG if cfg.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="ruyi-backend",
        description="CLI management client for RuyiSDK backend services.",
    )
    sp = parser.add_subparsers(title="subcommands", required=True)

    psw = sp.add_parser(
        "password",
        help="Utilities for working with passwords.",
    )
    psw_sp = psw.add_subparsers(title="subcommands", required=True)
    psw_sp.add_parser(
        "hash",
        help="Hash a password for storage.",
    ).set_defaults(func=do_hash_password)
    psw_test = psw_sp.add_parser(
        "test",
        help="Test a password against a generated hash.",
    )
    psw_test.set_defaults(func=do_test_password)
    psw_test.add_argument(
        "--hash",
        required=True,
        help="The hash to test against.",
    )

    sp.add_parser(
        "sync-releases",
        help="Release worker: sync releases from GitHub to the configured rsync destination.",
    ).set_defaults(
        func=lambda _: asyncio.run(
            do_sync_releases(
                cfg.cli.release_worker,
                cfg.github.ruyi_pm_repo,
            )
        ),
    )

    args = parser.parse_args(argv[1:])
    fn: Callable[[argparse.Namespace], int] = args.func
    return fn(args)


def entrypoint() -> NoReturn:
    """Script entrypoint for the ruyi-backend CLI."""

    sys.exit(main(sys.argv))
