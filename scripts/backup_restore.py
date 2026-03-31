import argparse
import shutil
from datetime import datetime
from pathlib import Path


def backup(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    target = backup_dir / f"pharmacy-{stamp}.db"
    shutil.copy2(db_path, target)
    return target


def restore(backup_file: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_file, db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup or restore pharmacy DB")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backup")
    b.add_argument("--db", default="data/pharmacy.db")
    b.add_argument("--out", default="backups")

    r = sub.add_parser("restore")
    r.add_argument("--file", required=True)
    r.add_argument("--db", default="data/pharmacy.db")

    args = parser.parse_args()
    if args.cmd == "backup":
        result = backup(Path(args.db), Path(args.out))
        print(f"backup_created={result}")
    else:
        restore(Path(args.file), Path(args.db))
        print("restore_completed=true")


if __name__ == "__main__":
    main()
