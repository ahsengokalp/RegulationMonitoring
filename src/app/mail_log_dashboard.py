from __future__ import annotations

from src.notify.mail_log import write_dashboard_from_events


def main() -> None:
    path = write_dashboard_from_events()
    print(path)


if __name__ == "__main__":
    main()
