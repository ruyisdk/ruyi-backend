import argparse
from _typeshed import Incomplete

TYPE_CHECKING: bool
cli: Incomplete
subparsers: Incomplete

def argument(*name_or_flags, **kwargs): ...
def subcommand(args=None, parent=...): ...

FORMATS: Incomplete
arg_start_date: Incomplete
arg_end_date: Incomplete
arg_month: Incomplete
arg_last_month: Incomplete
arg_this_month: Incomplete
arg_json: Incomplete
arg_daily: Incomplete
arg_monthly: Incomplete
arg_format: Incomplete
arg_color: Incomplete
arg_verbose: Incomplete
package_argument: Incomplete
common_arguments: Incomplete

def recent(args: argparse.Namespace) -> None: ...
def overall(args: argparse.Namespace) -> None: ...
def python_major(args: argparse.Namespace) -> None: ...
def python_minor(args: argparse.Namespace) -> None: ...
def system(args: argparse.Namespace) -> None: ...
def main() -> None: ...
