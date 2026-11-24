"""Import the next month only after it appears in the official CRTC catalogue."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import lzma
import re
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, urlopen
from zipfile import ZipFile
from logs import ROOT, STATIONS, station_days

ARCHIVES = ROOT / "snapshots"
CATALOGUE = "https://open.canada.ca/data/api/action/package_show?id=800106c1-0b08-401e-8be2-ac45d62e662e"


def published_months(document):
    if document.get("success") is not True:
        raise ValueError("Official archive catalogue was not successfully retrieved")
    months = {}
    for resource in document["result"]["resources"]:
        month = resource.get("name", "")
        if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month):
            continue
        expected = f"https://applications.crtc.gc.ca/OpenData/Television%20Logs/STAR2/{month[:4]}/{month}.zip"
        if resource.get("url", "").replace(" ", "%20") != expected:
            raise ValueError(f"Review changed official archive URL for {month}")
        months[month] = expected
    if not months:
        raise ValueError("Official catalogue contains no television log months")
    return months


def check_publication(current, month, fetch=urlopen):
    request = Request(CATALOGUE, headers={"User-Agent": "CoolCode Air Check Diary"})
    with fetch(request, timeout=60) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Official catalogue exceeded its size limit")
    months = published_months(json.loads(raw))
    if current not in months:
        raise ValueError("Previously retained month is absent from the official catalogue")
    if month not in months and max(months) > month:
        raise ValueError("Official archive catalogue has a gap before a later month")
    return months


def record_check(months, current, status):
    document = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "catalogue": CATALOGUE, "latest_published": max(months),
                "latest_retained": current, "status": status}
    pending = ARCHIVES / "check.tmp"
    pending.write_text(json.dumps(document, indent=2) + "\n")
    pending.replace(ARCHIVES / "check.json")


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
    current = max(x.name for x in ARCHIVES.glob("????-??"))
    month = args.month or next_month(current)
    datetime.strptime(month, "%Y-%m")
    months = None
    if not args.month and not args.zip:
        months = check_publication(current, month)
        if month not in months:
            record_check(months, current, "awaiting_publication")
            print(f"Checked official catalogue: {current} is the latest published month; {month} is not published yet")
            return
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
    if months is not None:
        record_check(months, max(current, month), "imported")


if __name__ == "__main__":
    main()
