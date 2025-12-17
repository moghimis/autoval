import argparse
from typing import Optional, Sequence

from autoval.dashboard.app import create_dash_app


def main(argv: Optional[Sequence[str]] = None):
    parser = argparse.ArgumentParser(prog="autoval", description="Autoval command line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dash_parser = subparsers.add_parser("dashboard", help="Launch the Dash dashboard.")
    dash_parser.add_argument("--bundle", required=True, help="Path to the report bundle directory.")
    dash_parser.add_argument("--host", default="127.0.0.1")
    dash_parser.add_argument("--port", type=int, default=8050)
    dash_parser.add_argument("--debug", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "dashboard":
        app = create_dash_app(args.bundle)
        app.run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
