from __future__ import annotations

import argparse
import logging
import sys

# Suppress Flask/Werkzeug development server warning — this tool is local-only
logging.getLogger("werkzeug").setLevel(logging.ERROR)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="cert-generator",
        description="AWS UG Certificate Generator CLI",
    )
    sub = ap.add_subparsers(dest="command", metavar="COMMAND")

    start_p = sub.add_parser("start", help="Start the local web server")
    start_p.add_argument("--port", type=int, default=5050, help="Port to listen on (default: 5050)")
    start_p.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")

    args = ap.parse_args()

    if args.command == "start":
        from app import app
        print("=" * 50)
        print("  AWS UG Certificate Generator")
        print("=" * 50)
        print(f"  URL  : http://localhost:{args.port}")
        print("  Press Ctrl+C to stop")
        print("=" * 50)
        app.run(debug=False, host=args.host, port=args.port)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
