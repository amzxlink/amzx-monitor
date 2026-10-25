import datetime as dt
import unittest
from unittest.mock import Mock
import monitor
import watchdog

NOW = dt.datetime(2026,10,25,0,0,tzinfo=dt.timezone.utc)
URL = 'https://hc-ping.com/12345678-1234-1234-1234-123456789abc'

class Response:
    status=200
    def __init__(self, url='https://example.org/', body=b'OK'): self.url=url; self.body=body
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def geturl(self): return self.url
    def read(self,*args): return self.body

class WatchdogTests(unittest.TestCase):
    def state(self): return {'_monitor':{'completed_at':NOW.isoformat(),'completed_run_id':'42'}}
    def env(self,url=URL): return {'MONITOR_HEARTBEAT_URL':url,'GITHUB_RUN_ID':'42'}
    def test_first_run_no_gap(self):
        m={}; watchdog.recovery(m,NOW); self.assertNotIn('pending',m)
    def test_normal_schedule_no_gap(self):
        m={'completed_at':(NOW-dt.timedelta(minutes=5)).isoformat()}; watchdog.recovery(m,NOW); self.assertNotIn('pending',m)
    def test_recovery_gap(self):
        m={'completed_at':(NOW-dt.timedelta(minutes=25)).isoformat()}; watchdog.recovery(m,NOW); self.assertEqual(len(m['pending']),1); self.assertEqual(m['last_gap']['seconds'],1500)
    def test_migration_gap(self):
        m={}; watchdog.recovery(m,NOW,[(NOW-dt.timedelta(minutes=30)).isoformat()]); self.assertEqual(len(m['pending']),1)
    def test_bad_timestamp(self):
        m={'completed_at':'bad'}; watchdog.recovery(m,NOW); self.assertNotIn('pending',m)
    def test_disabled_no_request(self):
        send=Mock(); self.assertTrue(watchdog.heartbeat({},environ={},opener=send,now=NOW)); send.assert_not_called()
    def test_success(self):
        send=Mock(return_value=Response()); self.assertTrue(watchdog.heartbeat(self.state(),self.env(),send,NOW)); self.assertEqual(send.call_count,1)
    def test_bad_host(self):
        send=Mock(); self.assertFalse(watchdog.heartbeat(self.state(),self.env('https://evil.test/private'),send,NOW)); send.assert_not_called()
    def test_wrong_run_no_request(self):
        s=self.state(); s['_monitor']['completed_run_id']='41'; send=Mock(); self.assertFalse(watchdog.heartbeat(s,self.env(),send,NOW)); send.assert_not_called()
    def test_stale_no_request(self):
        s=self.state(); s['_monitor']['completed_at']=(NOW-dt.timedelta(minutes=11)).isoformat(); send=Mock(); self.assertFalse(watchdog.heartbeat(s,self.env(),send,NOW)); send.assert_not_called()
    def test_missing_completion(self):
        self.assertFalse(watchdog.heartbeat({},self.env(),Mock(),NOW))
    def test_network_retry_bounded(self):
        send=Mock(side_effect=OSError('private URL')); self.assertFalse(watchdog.heartbeat(self.state(),self.env(),send,NOW)); self.assertEqual(send.call_count,3)
    def test_redirect_not_followed(self):
        self.assertIsNone(watchdog.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test'))
    def test_known_redirect(self):
        target={'url':'https://short.test/abc','expected_text':'OK','expected_final_url':'https://example.org/'}
        self.assertTrue(monitor.probe(target,lambda *a,**k:Response())[0])
    def test_wrong_redirect(self):
        target={'url':'https://short.test/abc','expected_text':'OK','expected_final_url':'https://example.org/correct'}
        self.assertFalse(monitor.probe(target,lambda *a,**k:Response())[0])
    def test_error_page_despite_200(self):
        target={'url':'https://example.org/','expected_text':'OK','forbidden_texts':['Composer detected issues in your platform']}
        self.assertFalse(monitor.probe(target,lambda *a,**k:Response(body=b'OK Composer detected issues in your platform'))[0])
    def test_invalid_destination_config(self):
        with self.assertRaises(ValueError): monitor.validate({'targets':[{'id':'a','url':'https://short.test/a','expected_text':'OK','expected_final_url':'http://example.org/'}]})
    def test_invalid_forbidden(self):
        with self.assertRaises(ValueError): monitor.validate({'targets':[{'id':'a','url':'https://example.org/','expected_text':'OK','forbidden_texts':'bad'}]})

if __name__=='__main__': unittest.main()
