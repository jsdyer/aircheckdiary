# Aircheck Diary

Compare Canadian television schedules on the local station clock, search a full month of titles and inspect the source rows for an airing. [Open Aircheck Diary](https://coolcode.ca/aircheckdiary/)

<!-- coolcode:guide -->
Compare September 1, 2026 at 8 p.m. Halifax’s CJCH logged Password while Vancouver’s CIVT logged Jeopardy! Masters. At 10 p.m. the titles trade places. Open a program’s source rows to see the commercial spots and segments filed inside its slot.
The official catalogue is checked separately from the retained archive date; an unpublished next month is reported as awaiting publication.
<!-- /coolcode:guide -->

## Try a comparison

| Local clock on September 1 | Halifax | Vancouver |
| --- | --- | --- |
| [8 p.m. on CTV](https://coolcode.ca/aircheckdiary/?a=CJCH&b=CIVT&date=2026-09-01&t=72000) | Password | Jeopardy! Masters |
| [10 p.m. on CTV](https://coolcode.ca/aircheckdiary/?a=CJCH&b=CIVT&date=2026-09-01&t=79200) | Jeopardy! Masters | Password |
| [6 a.m. on CBC](https://coolcode.ca/aircheckdiary/?a=CBHT&b=CBUT&date=2026-09-01&t=21600) | Information Morning Nova Scotia | The Early Edition (Vancouver) |
| [8 p.m. on CBC](https://coolcode.ca/aircheckdiary/?a=CBHT&b=CBUT&date=2026-09-01&t=72000) | Still Standing | Still Standing |

The before and after buttons select the neighbouring program and update both cards. The title search covers all four stations for the selected month, including distinct segment titles. Select an airing to open the parent program. Open the full schedules to jump to any logged start or copy the comparison link to share the stations, date and time. Search terms stay in the browser. The site fetches public day files and the title index from its own host.

## What the edition covers

The September 2026 CRTC archive contained 221 log files and 74,225,335 bytes. The four selected stations filed 128,048 nonblank records across 120 station-days. They include 5,749 program starts. The original reporting dates run from September 1 through September 30. The archive was retrieved November 19, 2026.

These are licensees’ filed accounts of broadcasts. Titles, misspellings, clocks, durations, record codes and the other fixed-width fields appear as submitted. Opening a source entry gives its original text, physical line number and station filename. The checked-in compressed extracts retain the original station files byte for byte. The inventory also records the ZIP digest.

[Original September ZIP](https://applications.crtc.gc.ca/OpenData/Television%20Logs/STAR2/2026/2026-09.zip) · [Federal data catalogue](https://open.canada.ca/data/en/dataset/800106c1-0b08-401e-8be2-ac45d62e662e) · [CRTC logging guide](https://crtc.gc.ca/eng/5000/tv14.htm) · [Program categories](https://crtc.gc.ca/canrec/eng/tvcat.htm) · [Site inventory](https://coolcode.ca/aircheckdiary/data/archive.json)

## Reading the time and record codes

Both cards use the selected local clock and reporting date. Halifax uses Atlantic time and Vancouver uses Pacific time. In September, 8 p.m. local in the two cities occurs four hours apart. The reporting clock rolls over at 5 a.m. for the two CTV logs and 6 a.m. for the two CBC logs. After midnight, the original reporting date stays on each row. “Next day” means the following civil date. A comparison outside a selected station’s reporting interval displays a gap.

PGR (program), PFS (first segment) and PGI (paid program) start a slot. Consecutive SEG continuation records extend a PFS to its last filed segment end. Each spot is attached to the slot containing its local start. The start and end boundaries define the slot. Adding commercial durations would count the same airtime twice. The interface retains COM, NRN, PRC, PRO and any other filed types. Rows outside a slot remain accessible in the full schedule. Some stations leave the filed end clock blank for spots. The original blank and the filed duration remain visible.

## Build and refresh

Run `python3 scripts/build.py` to build the site from checked-in snapshots without network access. Serve `dist/` with `python3 -m http.server --directory dist`. The build writes one gzip JSON file for each station and reporting date plus one searchable title index per month. Modern browsers open the compressed records on demand.

Run `python3 -m unittest discover -s tests -v` and `node --test tests/*.test.mjs` for the importer and comparison checks. CI also exercises the published layout at a project subpath with Playwright.

The monthly workflow checks the official federal catalogue before importing the next consecutive month, validates every station and builds the edition before saving it. If the next month has not been published, the check succeeds with `awaiting_publication`; the retained data and their retrieval dates remain unchanged. A listed archive that cannot be downloaded still fails. `data/check.json` exposes the actual catalogue check time separately from `data/archive.json` and its archive retrieval dates. Earlier months remain selectable. If an upstream file is missing or changes format, the previous edition stays available. Run `python3 scripts/refresh.py --month YYYY-MM` to retrieve a specified ZIP, or add `--zip /path/to/month.zip --retrieved YYYY-MM-DD` to use a downloaded archive. The workflow supports manual backfills and revised editions.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. The independent scheduler on our Linux server triggers overdue refreshes and checks published freshness; its code and current target list live in [the hub repository](https://github.com/jsdyer/jsdyer.github.io/tree/main/services/refresh-watchdog). The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
