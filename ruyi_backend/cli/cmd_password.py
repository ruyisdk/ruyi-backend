import argparse
import getpass

from ..components.auth import check_password, gen_password_hash


def do_hash_password(_args: argparse.Namespace) -> int:
    password = getpass.getpass("Password: ")
    h = gen_password_hash(password)
    print(h)
    return 0


def do_test_password(args: argparse.Namespace) -> int:
    h = args.hash
    password = getpass.getpass("Password: ")
    if check_password(h, password):
        print("Password matches")
        return 0
    print("Password does not match")
    return 1
