from __future__ import annotations

from . import create_app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":  # pragma: no cover - dev entrypoint
    main()

