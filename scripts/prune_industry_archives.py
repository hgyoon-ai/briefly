import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_TABS = ["ai", "finance", "semiconductor", "ev", "realestate"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prune industry archive JSON files older than N days."
    )
    parser.add_argument("--keep-days", type=int, default=90)
    parser.add_argument("--tz", type=str, default="Asia/Seoul")
    parser.add_argument("--archive-root", type=str, default="archive/industry")
    parser.add_argument(
        "--tabs",
        type=str,
        default=",".join(DEFAULT_TABS),
        help="Comma-separated tab list (default: ai,finance,semiconductor,ev,realestate)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print deletions without removing files",
    )
    return parser.parse_args()


def iter_archive_json_files(tab_root: Path):
    # Archive filenames follow: {YYYY-MM-DD}_{period}.json
    for path in tab_root.rglob("*_*.json"):
        if path.is_file():
            yield path


def parse_archive_date(filename: str):
    if "_" not in filename:
        return None
    date_part = filename.split("_", 1)[0]
    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None


def remove_empty_dirs(root: Path):
    # Remove empty leaf directories bottom-up.
    dirs = [p for p in root.rglob("*") if p.is_dir()]
    for d in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        try:
            next(d.iterdir())
        except StopIteration:
            d.rmdir()


def main():
    args = parse_args()

    keep_days = int(args.keep_days)
    if keep_days < 0:
        raise SystemExit("--keep-days must be >= 0")

    tz = ZoneInfo(args.tz)
    today = datetime.now(tz).date()
    cutoff = today - timedelta(days=keep_days)

    archive_root = Path(args.archive_root)
    tabs = [t.strip() for t in (args.tabs or "").split(",") if t.strip()]
    if not tabs:
        tabs = list(DEFAULT_TABS)

    scanned = 0
    deleted = 0

    for tab in tabs:
        tab_root = archive_root / tab
        if not tab_root.exists():
            continue

        for path in iter_archive_json_files(tab_root):
            scanned += 1
            file_date = parse_archive_date(path.name)
            if not file_date:
                continue
            if file_date >= cutoff:
                continue

            if args.dry_run:
                print(f"[dry-run] delete {path}")
                deleted += 1
                continue

            path.unlink(missing_ok=True)
            deleted += 1

    if not args.dry_run and archive_root.exists():
        for tab in tabs:
            tab_root = archive_root / tab
            if tab_root.exists():
                remove_empty_dirs(tab_root)

    print(
        f"[prune] keep_days={keep_days} today={today} cutoff={cutoff} scanned={scanned} deleted={deleted} dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
