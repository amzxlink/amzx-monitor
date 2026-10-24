import io
import json
import unittest
from unittest.mock import patch
import urllib.error
import monitor as m

class Response(io.BytesIO):
    status = 200
    def geturl(self): return 'https://amzx.link/'

class Tests(unittest.TestCase):
    target = {'url': 'https://amzx.link/', 'expected_text': 'AMZX'}
    def test_online(self):
        self.assertTrue(m.probe(self.target, lambda *a, **k: Response(b'<title>amzx</title>'))[0])
    def test_false_200(self):
        self.assertFalse(m.probe(self.target, lambda *a, **k: Response(b'error page'))[0])
    def test_http_520(self):
        def bad(*a, **k): raise urllib.error.HTTPError('', 520, '', {}, None)
        self.assertEqual(m.probe(self.target, bad)[1], 'HTTP 520')
    def test_timeout(self):
        def bad(*a, **k): raise TimeoutError()
        self.assertFalse(m.probe(self.target, bad)[0])
    def test_redirect(self):
        class Other(Response):
            def geturl(self): return 'https://other.example/'
        self.assertFalse(m.probe(self.target, lambda *a, **k: Other(b'AMZX'))[0])
    def test_insecure_redirect(self):
        class Other(Response):
            def geturl(self): return 'http://amzx.link/'
        self.assertFalse(m.probe(self.target, lambda *a, **k: Other(b'AMZX'))[0])
    def test_three_attempts(self):
        calls=[]
        def bad(t): calls.append(1); return False, 'HTTP 500', 0
        self.assertFalse(m.check(self.target, bad, lambda s: None)[0])
        self.assertEqual(len(calls), 3)
    def test_retry_recovers(self):
        results=iter([(False,'error',0),(True,'ok',0)])
        self.assertTrue(m.check(self.target, lambda t: next(results), lambda s: None)[0])
    def test_first_online(self):
        self.assertEqual(len(m.transition(None, True, 'ok', 'now', 'AMZX')['pending']), 1)
    def test_first_offline(self):
        self.assertEqual(m.transition(None, False, 'error', 'now', 'AMZX')['down_since'], 'now')
    def test_no_spam(self):
        s=m.transition(None, True, 'ok', 'now', 'AMZX'); s['pending']=[]
        self.assertEqual(m.transition(s, True, 'ok', 'later', 'AMZX')['pending'], [])
    def test_down_and_recovery(self):
        s=m.transition({'status':'online'}, False, 'error','down','AMZX')
        s['pending']=[]
        s=m.transition(s, True, 'ok','up','AMZX')
        self.assertIn('voltou', s['pending'][0]); self.assertNotIn('down_since',s)
    def test_failed_delivery_keeps_queue(self):
        s={'pending':['one','two']}
        self.assertFalse(m.flush(s, lambda x: False)); self.assertEqual(len(s['pending']),2)
    def test_delivery_clears_queue(self):
        s={'pending':['one','two']}; sent=[]
        self.assertTrue(m.flush(s, lambda x: sent.append(x) or True)); self.assertEqual(sent,['one','two']); self.assertEqual(s['pending'],[])
    def test_missing_secrets(self):
        with patch.dict('os.environ', {}, clear=True): self.assertFalse(m.telegram('test'))
    def test_telegram_success(self):
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN':'fake','TELEGRAM_CHAT_ID':'123'}):
            self.assertTrue(m.telegram('test', lambda *a, **k: Response(b'{"ok":true}')))
    def test_telegram_rejected(self):
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN':'fake','TELEGRAM_CHAT_ID':'123'}):
            self.assertFalse(m.telegram('test', lambda *a, **k: Response(b'{"ok":false}')))
    def test_persistent_state(self):
        s=m.transition(None,False,'error','now','AMZX')
        self.assertEqual(json.loads(json.dumps(s)),s)

if __name__ == '__main__': unittest.main()
