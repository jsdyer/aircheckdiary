from pathlib import Path
import shutil
import tempfile
from logs import ROOT, STATIONS, build_month, packed


def main():
    with tempfile.TemporaryDirectory(dir=ROOT) as work:
        site = Path(work) / "site"
        shutil.copytree(ROOT / "web", site)
        data = site / "data"
        editions = [build_month(folder, data) for folder in sorted((ROOT / "snapshots").glob("????-??"))]
        if not editions:
            raise ValueError("No archived months")
        latest = editions[-1]
        summary = {"first": editions[0]["first"], "last": latest["last"],
                   "retrieved": max(m["retrieved"] for m in editions),
                   "count": sum(m["count"] for m in editions), "rows": sum(m["rows"] for m in editions),
                   "stationDays": sum(m["stationDays"] for m in editions), "stations": STATIONS, "editions": editions}
        (data / "archive.json").write_bytes(packed(summary))
        check = ROOT / "snapshots/check.json"
        if check.exists():
            shutil.copy(check, data / "check.json")
        shutil.copy(ROOT / "tool.json", site)
        (site / ".nojekyll").touch()
        shutil.rmtree(ROOT / "dist", ignore_errors=True)
        site.rename(ROOT / "dist")
        print(f"{summary['count']:,} program starts; {summary['rows']:,} source rows; {summary['stationDays']} station-days")


if __name__ == "__main__":
    main()
