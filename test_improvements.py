import datetime as dt
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import monitor as m

UTC=dt.timezone.utc
NOW=dt.datetime(2026,10,24,12,3,tzinfo=UTC)
class Improvements(unittest.TestCase):
    def test_slow_three_samples(self):
        s={'pending':[]}
        for _ in range(2): m.latency(s,True,6,{},'Bio')
        self.assertEqual(s['pending'],[])
        m.latency(s,True,6,{},'Bio'); self.assertEqual(len(s['pending']),1)
        m.latency(s,True,9,{},'Bio'); self.assertEqual(len(s['pending']),1)
    def test_slow_recovery(self):
        s={'pending':[],'slow_active':True}
        m.latency(s,True,1,{},'Bio'); self.assertFalse(s['slow_active']); self.assertIn('normalizado',s['pending'][0])
    def test_failed_request_resets_slow(self):
        s={'pending':[],'slow_active':True,'slow_count':2}
        m.latency(s,False,20,{},'Bio'); self.assertEqual(s['slow_count'],0); self.assertFalse(s['slow_active'])
    def test_tls_valid(self):
        s={'pending':[]}; m.tls_check(s,{'amzx.link'},NOW,fetch=lambda h:NOW.timestamp()+90*86400)
        self.assertEqual(s['pending'],[])
    def test_tls_warning_once_daily(self):
        s={'pending':[]}; f=lambda h: NOW.timestamp()+10*86400
        m.tls_check(s,{'amzx.link'},NOW,fetch=f)
        m.tls_check(s,{'amzx.link'},NOW,fetch=lambda h:self.fail('consultou duas vezes'))
        self.assertEqual(len(s['pending']),1)
    def test_tls_escalation(self):
        s={'pending':[]}; m.tls_check(s,{'amzx.link'},NOW,fetch=lambda h:NOW.timestamp()+10*86400)
        tomorrow=NOW+dt.timedelta(days=1)
        m.tls_check(s,{'amzx.link'},tomorrow,fetch=lambda h:tomorrow.timestamp()+2*86400)
        self.assertEqual(len(s['pending']),2)
    def test_tls_renewal(self):
        s={'pending':[],'certificates':{'amzx.link':{'alert_level':'warning'}}}
        m.tls_check(s,{'amzx.link'},NOW,fetch=lambda h:NOW.timestamp()+90*86400)
        self.assertIn('válido',s['pending'][0])
    def test_tls_network_error(self):
        def bad(h): raise OSError('private detail')
        s={'pending':[]}; m.tls_check(s,{'amzx.link'},NOW,fetch=bad)
        self.assertEqual(s['certificates']['amzx.link']['alert_level'],'error'); self.assertNotIn('private',str(s))
    def test_summary_once(self):
        s={'pending':[]}; target=[{'id':'amzx','name':'AMZX'}]
        m.daily_summary(s,[],target,NOW,{})
        m.daily_summary(s,[],target,NOW,{})
        self.assertEqual(len(s['pending']),1); self.assertIn('sem medições',s['pending'][0])
    def test_summary_before_eight(self):
        s={'pending':[]}; m.daily_summary(s,[],[],NOW-dt.timedelta(hours=1),{}); self.assertEqual(s['pending'],[])
    def test_summary_manaus_date_and_coverage(self):
        rows=[{'id':'amzx','time':'2026-10-24T02:00:00+00:00','online':True,'seconds':1},
              {'id':'amzx','time':'2026-10-24T02:06:00+00:00','online':False,'seconds':20}]
        s={'pending':[]}; m.daily_summary(s,rows,[{'id':'amzx','name':'AMZX'}],NOW,{})
        self.assertIn('2026-10-23',s['pending'][0]); self.assertIn('50.0%',s['pending'][0]); self.assertIn('0.7%',s['pending'][0])
    def test_migration_does_not_reactivate(self):
        old={'status':'online','checked_at':'old','pending':[]}
        s=m.transition(old,True,'ok',NOW.isoformat(),'AMZX'); self.assertEqual(s['pending'],[])
    def test_duration(self):
        old={'status':'offline','down_since':(NOW-dt.timedelta(minutes=7)).isoformat(),'pending':[]}
        s=m.transition(old,True,'ok',NOW.isoformat(),'AMZX'); self.assertIn('7 min 0 s',s['pending'][0])
    def test_diagnostic_does_not_leak_remote_error(self):
        def bad(*a,**k): raise urllib.error.HTTPError('https://private-token',403,'private-secret',{},None)
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'private-token','TELEGRAM_CHAT_ID':'private-chat'}),patch('sys.stdout',new_callable=io.StringIO) as out:
            self.assertFalse(m.telegram('text',bad)); self.assertIn('403',out.getvalue()); self.assertNotIn('private',out.getvalue())
    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data/state.json'; m.write_json(path,{'ok':True}); self.assertEqual(json.loads(path.read_text()),{'ok':True}); self.assertFalse(path.with_suffix('.tmp').exists())
    def test_config(self):
        self.assertEqual(len(m.validate(json.loads(Path('config.json').read_text()))),3)
    def test_bad_url(self):
        for url in ['http://example.org','https://user:pass@example.org/','https://example.org/?token=private']:
            with self.assertRaises(ValueError): m.validate({'targets':[{'id':'a','url':url,'expected_text':'ok'}]})
    def test_duplicate_id(self):
        t={'id':'a','url':'https://example.org','expected_text':'ok'}
        with self.assertRaises(ValueError): m.validate({'targets':[t,t]})
    def test_main_preserves_v1_and_new_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            config={'targets':[{'id':'amzx','name':'AMZX','url':'https://amzx.link/','expected_text':'AMZX'}]}
            old=Path.cwd()
            try:
                os.chdir(tmp); Path('config.json').write_text(json.dumps(config)); Path('data').mkdir()
                Path('data/state.json').write_text(json.dumps({'amzx':{'status':'online','pending':[]}}))
                with patch.object(m,'check',return_value=(True,'ok',1)),patch.object(m,'tls_check'),patch.object(m,'daily_summary'),patch.object(m,'flush',return_value=True):
                    self.assertEqual(m.main(),0)
                result=json.loads(Path('data/state.json').read_text()); self.assertEqual(result['amzx']['status'],'online'); self.assertEqual(result['amzx']['pending'],[]); self.assertIn('_monitor',result)
            finally: os.chdir(old)
    def test_pending_persisted_if_delivery_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old=Path.cwd()
            try:
                os.chdir(tmp); Path('config.json').write_text(json.dumps({'targets':[{'id':'a','name':'A','url':'https://example.org','expected_text':'A'}]}))
                with patch.object(m,'check',return_value=(True,'ok',1)),patch.object(m,'tls_check'),patch.object(m,'daily_summary'),patch.object(m,'flush',return_value=False):
                    self.assertEqual(m.main(),1)
                self.assertEqual(len(json.loads(Path('data/state.json').read_text())['a']['pending']),1)
            finally: os.chdir(old)

if __name__=='__main__': unittest.main()
