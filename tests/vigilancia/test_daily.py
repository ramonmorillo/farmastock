import datetime,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'scripts/vigilancia'))
from daily import should_collect
UTC=datetime.timezone.utc
class DailyTests(unittest.TestCase):
 def test_winter_and_summer_once_per_madrid_day(self):
  for month in [1,7]:
   old={'checked_at':f'2026-{month:02}-10T10:00:00+00:00'}
   first=datetime.datetime(2026,month,11,6,10,tzinfo=UTC)
   self.assertEqual(should_collect(old,first),month==7)
   self.assertTrue(should_collect(old,first+datetime.timedelta(hours=1)))
   fresh={'checked_at':first.isoformat()}
   self.assertFalse(should_collect(fresh,first+datetime.timedelta(hours=1)))
 def test_capture_date_is_local_not_utc(self):
  # 23:30 UTC in July is already the next day in Madrid.
  snapshot={'checked_at':'2026-07-10T23:30:00+00:00'}
  self.assertFalse(should_collect(snapshot,datetime.datetime(2026,7,11,6,10,tzinfo=UTC)))
 def test_dispatch_same_day_can_force_explicit_test(self):
  s={'checked_at':'2026-11-11T09:00:00+00:00'}
  now=datetime.datetime(2026,11,11,10,tzinfo=UTC)
  self.assertFalse(should_collect(s,now));self.assertTrue(should_collect(s,now,force=True))
 def test_future_or_timezone_missing_rejected(self):
  now=datetime.datetime(2026,11,11,10,tzinfo=UTC)
  for text in ['2026-11-12T10:00:00+00:00','2026-11-10T10:00:00']:
   with self.assertRaises(ValueError):should_collect({'checked_at':text},now)
if __name__=='__main__':unittest.main()
