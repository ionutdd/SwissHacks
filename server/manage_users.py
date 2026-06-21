from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from .app import DEFAULT_DATABASE
from .security import EncryptionManager, hash_password
from .store import SignalWatchStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage SignalWatch application users.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create an authenticated user.")
    create.add_argument("--username", required=True)
    create.add_argument("--display-name", required=True)
    create.add_argument("--role", required=True, choices=["admin", "compliance", "rm", "auditor"])
    create.add_argument("--rm-id")
    list_parser = subparsers.add_parser("list", help="List users without password material.")
    list_parser.set_defaults(command="list")
    args = parser.parse_args()

    encryption = EncryptionManager.load_or_create(args.database.with_name("signalwatch.key"))
    store = SignalWatchStore(args.database, encryption)
    store.initialize()
    if args.command == "list":
        for user in store.users():
            print(f"{user['username']}\t{user['role']}\t{user.get('rm_id') or '-'}\t{user['display_name']}")
        return 0

    # Prompt once for the password and accept it without requiring a confirmation.
    # This simplifies scripted or automated user creation where interactive
    # confirmation can be problematic.
    password = getpass.getpass("Password: ")
    user = store.create_user(
        args.username,
        args.display_name,
        args.role,
        hash_password(password),
        args.rm_id,
    )
    store.append_audit(user["id"], "user.created", "user", user["id"], {"role": user["role"], "rm_id": user.get("rm_id")})
    print(f"Created {user['username']} ({user['role']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
