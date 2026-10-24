import json
import os
import unittest
from unittest.mock import patch
import push_delivery as p

class Push(unittest.TestCase):
    def state(self):return {'amzx':{'pending':['🔴 AMZX caiu']},'_monitor':{'pending':[]}}
    def test_disabled_without_secret(self):
        with patch.dict(os.environ,{},clear=True):self.assertIsNone(p.devices())
    def test_hashes_not_endpoints(self):
        with patch.dict(os.environ,{'AMZX_WEBPUSH_CONFIG':json.dumps({'devices':[{'subscription':{'endpoint':'https://fcm.googleapis.com/private'}}]})}):
            ids=p.devices();self.assertEqual(len(ids[0]),64);self.assertNotIn('private',str(ids))
    def test_bad_config(self):
        with patch.dict(os.environ,{'AMZX_WEBPUSH_CONFIG':'bad'}):
            with self.assertRaises(ValueError):p.devices()
    def test_device_limit(self):
        with patch.dict(os.environ,{'AMZX_WEBPUSH_CONFIG':'{"devices":[]}'}):
            with self.assertRaises(ValueError):p.devices()
    def test_queue_disabled(self):
        s=self.state();p.queue_events(s,['amzx'],None);self.assertEqual(s['_monitor']['push_queue'],[])
    def test_queue_independent_of_telegram(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);s['amzx']['pending']=[]
        self.assertEqual(len(s['_monitor']['push_queue']),1)
    def test_no_duplicate(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);p.queue_events(s,['amzx'],['hash']);self.assertEqual(len(s['_monitor']['push_queue']),1)
    def test_urgency(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertTrue(s['_monitor']['push_queue'][0]['payload']['urgent'])
    def test_delivery_success(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertTrue(p.deliver(s,['hash'],lambda _: [{'id':'hash','status':'sent'}]));self.assertEqual(s['_monitor']['push_queue'],[])
    def test_delivery_retry(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertFalse(p.deliver(s,['hash'],lambda _: []));self.assertEqual(len(s['_monitor']['push_queue']),1)
    def test_partial_success(self):
        s=self.state();p.queue_events(s,['amzx'],['a','b']);self.assertFalse(p.deliver(s,['a','b'],lambda _: [{'id':'a','status':'sent'},{'id':'b','status':'retry'}]));self.assertEqual(s['_monitor']['push_queue'][0]['remaining'],['b'])
    def test_expired(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertTrue(p.deliver(s,['hash'],lambda _: [{'id':'hash','status':'expired'}]));self.assertTrue(s['_monitor']['push_needs_renewal'])
    def test_removed_device(self):
        s=self.state();p.queue_events(s,['amzx'],['old']);self.assertTrue(p.deliver(s,['new'],lambda _: []))
    def test_fake_provider_result_ignored(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertFalse(p.deliver(s,['hash'],lambda _: [{'id':'other','status':'sent'}]))
    def test_bounded_payload(self):
        s=self.state();s['amzx']['pending']=['a'*5000];p.queue_events(s,['amzx'],['hash']);self.assertEqual(len(s['_monitor']['push_queue'][0]['payload']['body']),600)
    def test_no_private_data_in_public_state(self):
        s=self.state();p.queue_events(s,['amzx'],['hash']);self.assertNotIn('private_key',json.dumps(s));self.assertNotIn('subscription',json.dumps(s))
