import io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import refresh

def catalogue(*months):
 return {'success':True,'result':{'resources':[{'name':m,'url':f'https://applications.crtc.gc.ca/OpenData/Television Logs/STAR2/{m[:4]}/{m}.zip'} for m in months]}}
class PublicationTests(unittest.TestCase):
 def test_unpublished_next_month_is_a_successful_catalogue_check(self):
  data=catalogue('2026-09')
  months=refresh.check_publication('2026-09','2026-10',lambda *a,**k:io.BytesIO(json.dumps(data).encode()))
  self.assertEqual(list(months),['2026-09'])
 def test_published_next_month_is_selected(self):
  self.assertIn('2026-10',refresh.published_months(catalogue('2026-09','2026-10')))
 def test_missing_catalogue_or_changed_urls_are_errors(self):
  for data in ({'success':False},catalogue()):
   with self.assertRaises(ValueError):refresh.published_months(data)
  data=catalogue('2026-09');data['result']['resources'][0]['url']='https://example.com/file.zip'
  with self.assertRaises(ValueError):refresh.published_months(data)
 def test_gap_or_missing_retained_month_is_not_called_waiting(self):
  for data in (catalogue('2026-09','2026-11'),catalogue('2026-10')):
   with self.assertRaises(ValueError):refresh.check_publication('2026-09','2026-10',lambda *a,**k:io.BytesIO(json.dumps(data).encode()))
