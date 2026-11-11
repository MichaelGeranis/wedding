#!/usr/bin/env python3
"""Generate secrets for .env file."""

import secrets
import sys

import bcrypt


def generate_jwt_secret() -> str:
    """Generate a secure JWT secret key."""
    return secrets.token_hex(32)


def generate_password_hash(password: str) -> str:
    """Generate bcrypt hash for admin password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def main() -> None:
    """Generate and print secrets."""
    print("=" * 80)
    print("WEDDING API - SECRET GENERATOR")
    print("=" * 80)
    print()

    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    print("JWT_SECRET_KEY (copy to .env):")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()

    # Generate admin password hash
    print("Admin Password Setup:")
    print("-" * 80)

    if len(sys.argv) > 1:
        # Password provided as argument
        password = sys.argv[1]
        print(f"Using password from argument: {password}")
    else:
        # Prompt for password
        import getpass

        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm admin password: ")

        if password != confirm:
            print("ERROR: Passwords don't match!")
            sys.exit(1)

    if len(password) < 8:
        print("WARNING: Password should be at least 8 characters!")

    password_hash = generate_password_hash(password)
    print()
    print("ADMIN_PASSWORD_HASH (copy to .env):")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print()

    print("=" * 80)
    print("Add these lines to your backend/.env file")
    print("=" * 80)


if __name__ == "__main__":
    main()
