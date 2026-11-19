"""Read the fixed-width station logs and build a searchable local-clock edition."""
from bisect import bisect_right
from collections import defaultdict
from datetime import date
from pathlib import Path
import calendar
import gzip
import json
import lzma

ROOT = Path(__file__).resolve().parents[1]
STATIONS = {
    "CJCH": {"city": "Halifax", "network": "CTV", "zone": "America/Halifax"},
    "CIVT": {"city": "Vancouver", "network": "CTV", "zone": "America/Vancouver"},
    "CBHT": {"city": "Halifax", "network": "CBC", "zone": "America/Halifax"},
    "CBUT": {"city": "Vancouver", "network": "CBC", "zone": "America/Vancouver"},
}
STARTS = {"PGR", "PFS", "PGI"}


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def seconds(clock):
    h, m, s = (int(clock[i:i + 2]) for i in (0, 2, 4))
    if m >= 60 or s >= 60:
        raise ValueError(f"Bad clock {clock}")
    return h * 3600 + m * 60 + s


def station_days(raw, station, month):
    try:
        data = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        data = raw.decode("cp1252")
    days = defaultdict(list)
    for line_no, line in enumerate(data.split("\n"), 1):
        row = line.rstrip("\r")
        if not row.strip():
            continue
        if len(row) != 192 or row[6:12].strip() != station or row[0] != "2":
            raise ValueError(f"Unexpected format in {station} line {line_no}")
        stamp = row[12:18]
        day = date.fromisoformat(f"20{stamp[:2]}-{stamp[2:4]}-{stamp[4:]}").isoformat()
        if day[:7] != month:
            raise ValueError(f"Row outside requested month: {day}")
        days[day].append([line_no, row])
    year, mm = map(int, month.split("-"))
    if len(days) != calendar.monthrange(year, mm)[1]:
        raise ValueError(f"Incomplete month in {station}")
    return days


def make_day(records):
    # A reporting date spans a station-defined 24h day. Its first entry supplies
    # the local boundary. All source clocks, including blank end times, survive.
    boundary = seconds(records[0][1][18:24])
    def start(row):
        clock = seconds(row[18:24])
        return clock + (86400 if clock < boundary else 0)
    def end(row):
        at = start(row)
        if not row[24:30].strip():
            return at + seconds(row[30:36])
        clock = seconds(row[24:30])
        return at + (clock - at) % 86400

    slots = []
    segments = {}
    current = None
    for index, (_, row) in enumerate(records):
        code = row[1:4]
        if code in STARTS:
            current = {"i": index, "from": start(row), "to": end(row), "items": [index]}
            slots.append(current)
        elif code == "SEG" and current and records[current["i"]][1][1:4] == "PFS":
            current["to"] = max(current["to"], end(row))
            segments[index] = current
    slots.sort(key=lambda s: (s["from"], s["i"]))
    times = [slot["from"] for slot in slots]
    outside = []
    for index, (_, row) in enumerate(records):
        if row[1:4] in STARTS:
            continue
        t = start(row)
        n = bisect_right(times, t) - 1
        slot = segments.get(index)
        if slot is None and n >= 0 and t < slots[n]["to"]:
            slot = slots[n]
        if slot:
            slot["items"].append(index)
        else:
            outside.append(index)
    indexed = []
    for slot in slots:
        row = records[slot["i"]][1]
        titles = list(dict.fromkeys(records[i][1][36:86].strip() for i in slot["items"]
                                   if records[i][1][1:4] in STARTS | {"SEG"}))
        indexed.append([slot["from"], titles])
    return {"boundary": boundary, "rows": records, "slots": slots, "outside": outside}, indexed


def build_month(source, target):
    meta = json.loads((source / "archive.json").read_text())
    month = meta["month"]
    dest = target / month
    dest.mkdir(parents=True, exist_ok=True)
    title_index = defaultdict(list)
    dates = set()
    nrows = nslots = 0
    types = defaultdict(int)
    for station in STATIONS:
        days = station_days(lzma.decompress((source / f"{station}.xz").read_bytes()), station, month)
        (dest / station).mkdir(exist_ok=True)
        for day, records in days.items():
            daily, entries = make_day(records)
            dates.add(day)
            for _, raw in records:
                types[raw[1:4]] += 1
            nrows += len(records)
            nslots += len(entries)
            (dest / station / f"{day}.json.gz").write_bytes(gzip.compress(packed(daily), mtime=0))
            for t, titles in entries:
                for title in titles:
                    title_index[title].append([station, day, t])
    (dest / "titles.json.gz").write_bytes(gzip.compress(packed(title_index), mtime=0))
    return {**meta, "first": min(dates), "last": max(dates), "dates": sorted(dates),
            "stationDays": len(dates) * len(STATIONS), "count": nslots, "rows": nrows, "types": types}
