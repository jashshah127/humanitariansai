"""
Mint a JWT for /solve and /grade access.

Run locally (or via `render exec` against the deployed environment), never over HTTP --
minting is an operator action, not an API surface. See auth.py's docstring for why.

Usage:
    export JWT_SECRET=...          # must match the value set on the server
    python3 mint_token.py --sub jash --hours 24
    python3 mint_token.py --sub demo-link --hours 720   # 30 days, for a shared demo token
"""
import argparse
import os
import sys

# Absolute path, not relative -- a relative "engine" only resolves if the working
# directory happens to be physics-engine/ when this runs. PyCharm run configurations
# often use a different cwd, and when the relative path silently fails to add anything
# real to sys.path, Python falls through and can import an unrelated *installed*
# package that happens to also be named "auth" instead of failing loudly. Matches the
# absolute-path pattern server.py already uses for the same reason.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from jwt_auth import create_token


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sub", default="user", help="subject claim -- who/what this token identifies")
    p.add_argument("--hours", type=float, default=24, help="hours until expiry")
    args = p.parse_args()

    token = create_token({"sub": args.sub}, expires_in=int(args.hours * 3600))
    print(token)
    print(f"\n# expires in {args.hours} hours, subject={args.sub!r}", file=sys.stderr)
    print(f"# usage: curl -H 'Authorization: Bearer {token}' ...", file=sys.stderr)


if __name__ == "__main__":
    main()