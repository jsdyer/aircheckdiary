import lzma
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from logs import STATIONS, make_day, station_days


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = ROOT / 'snapshots/2026-09'
        cls.days = {s: station_days(lzma.decompress((src / (s + '.xz')).read_bytes()), s, '2026-09') for s in STATIONS}

    def test_full_source_coverage(self):
        self.assertEqual(sum(len(r) for days in self.days.values() for r in days.values()), 128048)
        for station, days in self.days.items():
            self.assertEqual(len(days), 30)
            for records in days.values():
                day, _ = make_day(records)
                indices = [i for slot in day['slots'] for i in slot['items']] + day['outside']
                self.assertEqual(sorted(indices), list(range(len(records))))
                self.assertTrue(all(s['to'] > s['from'] for s in day['slots']))

    def test_evening_and_overnight(self):
        for station, first, last in [('CJCH','Password','Jeopardy! Masters'),('CIVT','Jeopardy! Masters','Password'),
                                      ('CBHT','Still Standing','CBC News: The National'),('CBUT','Still Standing','CBC News: The National')]:
            day, _ = make_day(self.days[station]['2026-09-01'])
            def at(t):
                slot = next(s for s in day['slots'] if s['from'] <= t < s['to'])
                return day['rows'][slot['i']][1][36:86].strip()
            self.assertEqual(at(72000), first)
            self.assertEqual(at(79200), last)
            self.assertTrue(at(86401))
            self.assertTrue(all(s['from'] >= day['boundary'] for s in day['slots']))

    def test_segmented_program_and_original_row(self):
        day, _ = make_day(self.days['CJCH']['2026-09-01'])
        password = next(s for s in day['slots'] if s['from'] == 72000)
        self.assertEqual(password['to'], 75600)
        self.assertEqual(day['rows'][password['i']][0], 731)
        self.assertEqual({day['rows'][i][1][1:4] for i in password['items']} & {'PFS','SEG','COM'}, {'PFS','SEG','COM'})
