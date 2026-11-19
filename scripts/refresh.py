"""Import a complete month. The scheduled run tries the next unpublished month."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile
from logs import ROOT, STATIONS, station_days

ARCHIVES = ROOT / "snapshots"


def next_month(month):
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12)}-{number % 12 + 1:02}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--month")
    p.add_argument("--zip", type=Path)
    p.add_argument("--retrieved")
    args = p.parse_args()
    ARCHIVES.mkdir(exist_ok=True)
    month = args.month or next_month(max(x.name for x in ARCHIVES.glob("????-??")))
    datetime.strptime(month, "%Y-%m")
    url = f"https://applications.crtc.gc.ca/OpenData/Television%20Logs/STAR2/{month[:4]}/{month}.zip"
    with tempfile.TemporaryDirectory(dir=ARCHIVES) as work:
        temp = Path(work)
        archive = args.zip
        if not archive:
            archive = temp / "download.zip"
            with urlopen(url, timeout=180) as response, archive.open("wb") as f:
                shutil.copyfileobj(response, f)
        ready = temp / "edition"
        ready.mkdir()
        meta = {"month": month, "url": url, "retrieved": args.retrieved or datetime.now(timezone.utc).date().isoformat(),
                "archiveBytes": archive.stat().st_size, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": {}}
        with ZipFile(archive) as logs:
            names = [n for n in logs.namelist() if n.lower().endswith(".log")]
            meta["archiveLogs"] = len(names)
            for station in STATIONS:
                matches = [n for n in names if n.replace("\\", "/").split("/")[-1].startswith(station + "_" + month.replace("-", ""))]
                if len(matches) != 1:
                    raise ValueError(f"Expected one file for {station}, found {matches}")
                raw = logs.read(matches[0])
                station_days(raw, station, month)
                (ready / f"{station}.xz").write_bytes(lzma.compress(raw, preset=6))
                meta["files"][station] = matches[0]
        (ready / "archive.json").write_text(json.dumps(meta, indent=2) + "\n")
        target = ARCHIVES / month
        # Existing data are replaced only after the complete candidate validates.
        if target.exists():
            target.rename(temp / "previous")
        try:
            ready.rename(target)
        except OSError:
            if (temp / "previous").exists():
                (temp / "previous").rename(target)
            raise
    print(f"Imported {month} ({meta['archiveLogs']} station files in source ZIP)")


if __name__ == "__main__":
    main()
