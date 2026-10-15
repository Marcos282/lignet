import json
import socket
from datetime import timedelta
from unittest.mock import patch,MagicMock
from django.test import TestCase,SimpleTestCase,Client,override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.network import UnsafeURL
from .forms import MeasurementForm
from .models import Measurement,GlobalpingPolicy
from .validation import target,validate_dns
from .services import GlobalpingClient,APIError,APIResponse
from .results import normalize
from .limits import reserve_probes,LimitExceeded,fingerprint
from .tasks import create_measurement,poll_measurement,cleanup,expire_stalled

# Synthetic test fixtures, shaped from the official v1 OpenAPI specification.
# Never imported or served by production code.
PROBE={'country':'BR','city':'São Paulo','network':'Test network','asn':64500,'latitude':-23.5,'longitude':-46.6}
PING={'id':'actualRemote1','type':'ping','status':'finished','probesCount':1,'results':[{'probe':PROBE,'result':{'status':'finished','resolvedAddress':'1.1.1.1','stats':{'min':0,'avg':1.5,'max':2,'loss':0},'rawOutput':'raw result'}}]}
INPUT={'target':'example.com','kind':'ping','locations':['country:BR'],'probes':1,'record_type':'A','authorized':True}


class ValidationTests(SimpleTestCase):
    def test_private_and_unsafe_inputs(self):
        for value in ['127.0.0.1','10.0.0.2','192.168.1.1','169.254.169.254','100.64.0.1','224.0.0.1','0.0.0.0','::1','fe80::1','fc00::1','::ffff:8.8.8.8','2002:7f00:1::','localhost','x.local','a.internal','a.test','a.onion','example.com:80','user@example.com','http://example.com','2130706433','example.com/x','example.com\r\nx','-a.com','a..com']:
            with self.subTest(value=value),self.assertRaises(ValueError):target(value,'ping')
    def test_public_ips_and_idn(self):
        self.assertEqual(target('1.1.1.1','ping')[0],'1.1.1.1')
        self.assertEqual(target('2606:4700:4700::1111','ping')[0],'2606:4700:4700::1111')
        self.assertEqual(target('EXAMPLE.COM.','ping')[0],'example.com')
        self.assertEqual(target('ação.com.br','ping')[0],'xn--ao-siap.com.br')
    def test_http_url_options(self):
        self.assertEqual(target('http://example.com/path','http'),('example.com','HTTP','/path'))
        for value in ['https://user:pass@example.com','https://example.com:443','https://example.com/?token=secret','https://127.0.0.1']:
            with self.subTest(value=value),self.assertRaises(ValueError):target(value,'http')
    def test_form_all_types_use_official_parameters(self):
        for kind in ['ping','traceroute','dns','http']:
            form=MeasurementForm({**INPUT,'kind':kind},policy=GlobalpingPolicy())
            self.assertTrue(form.is_valid(),form.errors)
            payload=form.cleaned_data['payload']
            self.assertEqual(payload['locations'],[{'country':'BR'}]);self.assertEqual(payload['limit'],1)
            if kind=='dns':self.assertEqual(payload['measurementOptions'],{'query':{'type':'A'}})
            if kind=='http':self.assertEqual(payload['measurementOptions']['request']['method'],'HEAD')
    def test_arbitrary_options_and_limits_blocked(self):
        for changes in [{'probes':51},{'locations':['magic:internal']},{'locations':['world','country:BR']},{'authorized':False},{'kind':'mtr'},{'locations':['country:BR','country:US']},{'record_type':'ANY'}]:
            with self.subTest(changes=changes):
                self.assertFalse(MeasurementForm({**INPUT,**changes},policy=GlobalpingPolicy()).is_valid())
    def test_all_required_dns_types(self):
        for record in ['A','AAAA','MX','NS','TXT','CNAME']:
            form=MeasurementForm({**INPUT,'kind':'dns','record_type':record},policy=GlobalpingPolicy())
            self.assertTrue(form.is_valid(),form.errors);self.assertEqual(form.cleaned_data['payload']['measurementOptions']['query']['type'],record)


class NetworkValidationTests(TestCase):
    @patch('core.network.socket.getaddrinfo')
    def test_mixed_private_dns_denied(self,dns):
        dns.return_value=[(2,1,6,'',('1.1.1.1',443)),(2,1,6,'',('127.0.0.1',443))]
        for kind in ['ping','dns','http','traceroute']:
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_dns('example.com',kind)
    @patch('core.network.socket.getaddrinfo',side_effect=socket.gaierror(socket.EAI_NONAME,'no addresses'))
    def test_dns_only_no_address(self,dns):
        validate_dns('example.com','dns')
        with self.assertRaises(ValueError):validate_dns('example.com','ping')
    def test_administrator_block(self):
        from core.models import BlockedHost
        BlockedHost.objects.create(hostname='example.com',reason='abuse')
        with self.assertRaises(ValueError):validate_dns('example.com','ping')


class ResultTests(SimpleTestCase):
    def test_ping_zero_and_missing_not_fabricated(self):
        row=normalize(PING,'ping')['rows'][0]
        self.assertEqual(row['min'],0);self.assertEqual(row['loss'],0)
        missing=normalize({'results':[{'probe':{},'result':{'status':'failed'}}]},'ping')['rows'][0]
        self.assertIsNone(missing['avg']);self.assertIsNone(missing['loss']);self.assertIsNone(missing['latitude'])
    def test_trace_unanswered_hop(self):
        data={'results':[{'probe':PROBE,'result':{'status':'finished','hops':[{'resolvedAddress':None,'resolvedHostname':None,'timings':[]},{'resolvedAddress':'1.1.1.1','timings':[{'rtt':1},{'rtt':None}]}]}}]}
        hops=normalize(data,'traceroute')['rows'][0]['hops']
        self.assertTrue(hops[0]['no_reply']);self.assertFalse(hops[1]['no_reply']);self.assertEqual(hops[1]['rtts'],[1,None])
    def test_dns_comparison_ignores_ttl_order(self):
        a={'name':'example.com.','type':'A','class':'IN','ttl':30,'value':'1.1.1.1'}
        results=[{'probe':PROBE,'result':{'status':'finished','statusCode':0,'answers':[a],'resolver':'8.8.8.8'}},{'probe':PROBE,'result':{'status':'finished','statusCode':0,'answers':[{**a,'ttl':10}],'resolver':'1.1.1.1'}}]
        data=normalize({'results':results},'dns');self.assertFalse(data['dns_different']);self.assertEqual(data['rows'][0]['resolver'],'8.8.8.8')
        results[1]['result']['answers'][0]['value']='8.8.8.8'
        self.assertTrue(normalize({'results':results},'dns')['dns_different'])
    def test_dns_uncomparable_not_claimed_equal(self):
        self.assertIsNone(normalize({'results':[]},'dns')['dns_different'])
    def test_http_redirect_fields(self):
        data={'results':[{'probe':PROBE,'result':{'status':'finished','statusCode':301,'headers':{'Location':'https://example.com/new'},'timings':{'total':25,'tcp':0},'tls':None}}]}
        row=normalize(data,'http')['rows'][0]
        self.assertEqual(row['http_status'],301);self.assertEqual(row['location'],'https://example.com/new');self.assertEqual(row['timings']['tcp'],0);self.assertIsNone(row['timings']['tls'])
    def test_bad_coordinates_and_nan(self):
        row=normalize({'results':[{'probe':{'latitude':999,'longitude':float('nan')},'result':{}}]},'ping')['rows'][0]
        self.assertIsNone(row['latitude']);self.assertIsNone(row['longitude'])


class ClientTests(SimpleTestCase):
    def session_response(self,session,status=200,data=None,headers=None):
        response=MagicMock(status_code=status,headers=headers or {})
        response.iter_content.return_value=[json.dumps(data or {}).encode()]
        session.return_value.__enter__.return_value.request.return_value.__enter__.return_value=response
        return response
    @patch('globalping.services.requests.Session')
    def test_official_endpoint_anonymous_and_usage(self,session):
        self.session_response(session,202,{'id':'actualRemote1','probesCount':1},{'X-RateLimit-Consumed':'1','X-RateLimit-Remaining':'249'})
        r=GlobalpingClient().create({'limit':1})
        call=session.return_value.__enter__.return_value.request.call_args
        self.assertEqual(call.args,('POST','https://api.globalping.io/v1/measurements'))
        self.assertNotIn('Authorization',call.kwargs['headers']);self.assertFalse(call.kwargs['allow_redirects']);self.assertEqual(r.usage['remaining'],249)
    @patch('globalping.services.requests.Session')
    def test_etag_304(self,session):
        self.session_response(session,304)
        r=GlobalpingClient().get('actualRemote1','"etag"')
        self.assertEqual(r.status,304)
        self.assertEqual(session.return_value.__enter__.return_value.request.call_args.kwargs['headers']['If-None-Match'],'"etag"')
    @patch('globalping.services.requests.Session')
    def test_429_retry_after(self,session):
        self.session_response(session,429,headers={'Retry-After':'12','X-RateLimit-Remaining':'0'})
        with self.assertRaises(APIError) as caught:GlobalpingClient().create({'limit':1})
        self.assertEqual(caught.exception.retry_after,12);self.assertEqual(caught.exception.usage['remaining'],0)
    @patch('globalping.services.requests.Session')
    def test_upstream_error_not_leaked(self,session):
        self.session_response(session,500,{'private':'secret-value'})
        with self.assertRaises(APIError) as caught:GlobalpingClient().get('abc')
        self.assertNotIn('secret',str(caught.exception))
    @patch('globalping.services.requests.Session')
    def test_invalid_create_response(self,session):
        self.session_response(session,202,{'id':'../../internal','probesCount':1})
        with self.assertRaises(APIError):GlobalpingClient().create({'limit':1})
    @patch('globalping.services.requests.Session')
    def test_response_size_limit(self,session):
        r=self.session_response(session);r.iter_content.return_value=[b'x'*(2*1024*1024+1)]
        with self.assertRaises(APIError):GlobalpingClient().get('abc')
    @patch('globalping.services.requests.Session')
    def test_fixed_host_rejects_id_url(self,session):
        with self.assertRaises(APIError):GlobalpingClient().get('https://127.0.0.1')
        session.assert_not_called()


class PlatformTests(TestCase):
    def setUp(self):
        cache.clear()
        self.policy=GlobalpingPolicy.objects.create()
    def obj(self,**kwargs):
        data={'session_hash':'session','kind':'ping','target':'example.com','payload':{'type':'ping','target':'example.com','limit':1},'probes_requested':1,'expires_at':timezone.now()+timedelta(hours=24)}
        data.update(kwargs);return Measurement.objects.create(**data)
    def post(self,data=INPUT):
        return self.client.post('/api/globalping/medicoes/',json.dumps(data),content_type='application/json')
    def test_public_pages_canonical_and_map(self):
        from .views import PAGES
        for slug in PAGES:
            r=self.client.get('/ferramentas/'+slug+'/')
            self.assertEqual(r.status_code,200);self.assertContains(r,'id="gp-map"');self.assertContains(r,'application/ld+json');self.assertContains(r,'rel="canonical"');self.assertEqual(r['Referrer-Policy'],'strict-origin-when-cross-origin')
    def test_sitemap_includes_new_pages_only(self):
        r=self.client.get('/sitemap.xml');self.assertContains(r,'/ferramentas/ping-mundial/');self.assertNotContains(r,'/api/globalping/')
    @patch('globalping.views.create_measurement.delay')
    def test_start_async_and_private_session(self,queue):
        r=self.post();self.assertEqual(r.status_code,202);queue.assert_called_once()
        pk=r.json()['id'];self.assertEqual(Measurement.objects.get(pk=pk).status,'queued')
        status=self.client.get(f'/api/globalping/medicoes/{pk}/');self.assertEqual(status.status_code,200);self.assertIn('noindex',status['X-Robots-Tag']);self.assertEqual(status['Cache-Control'],'private, no-store')
        self.assertEqual(Client().get(f'/api/globalping/medicoes/{pk}/').status_code,404)
    @patch('globalping.views.create_measurement.delay')
    def test_csrf_required(self,queue):
        self.assertEqual(Client(enforce_csrf_checks=True).post('/api/globalping/medicoes/',json.dumps(INPUT),content_type='application/json').status_code,403);queue.assert_not_called()
    @patch('globalping.views.create_measurement.delay')
    def test_ip_limit(self,queue):
        self.policy.requests_per_hour=1;self.policy.save()
        self.assertEqual(self.post().status_code,202)
        self.assertEqual(self.post().status_code,429);self.assertEqual(queue.call_count,1)
    @patch('globalping.views.create_measurement.delay')
    def test_user_limit_across_ips(self,queue):
        self.policy.requests_per_hour=1;self.policy.save()
        user=get_user_model().objects.create_user('gp-user');self.client.force_login(user)
        self.assertEqual(self.post().status_code,202)
        self.assertEqual(self.client.post('/api/globalping/medicoes/',json.dumps(INPUT),content_type='application/json',REMOTE_ADDR='8.8.8.8').status_code,429)
    @patch('globalping.views.create_measurement.delay')
    def test_disabled(self,queue):
        self.policy.enabled=False;self.policy.save()
        self.assertEqual(self.post().status_code,503);queue.assert_not_called()
    @patch('globalping.views.limit_request',side_effect=ConnectionError())
    def test_cache_failure_fails_closed(self,limits):
        self.assertEqual(self.post().status_code,503);self.assertEqual(Measurement.objects.count(),0)
    def test_private_input_never_queued(self):
        self.assertEqual(self.post({**INPUT,'target':'127.0.0.1'}).status_code,400)
        self.assertEqual(Measurement.objects.count(),0)
    def test_history_excludes_other_sessions_and_expired(self):
        self.obj();r=self.client.get('/api/globalping/historico/');self.assertEqual(r.json()['measurements'],[])
    def test_owner_can_read_in_new_session(self):
        user=get_user_model().objects.create_user('owner');obj=self.obj(owner=user)
        self.client.force_login(user);self.assertEqual(self.client.get(f'/api/globalping/medicoes/{obj.pk}/').status_code,200)
    @patch('globalping.tasks.GlobalpingClient')
    def test_get_status_does_not_call_api(self,client):
        user=get_user_model().objects.create_user('reader');obj=self.obj(owner=user)
        self.client.force_login(user);self.client.get(f'/api/globalping/medicoes/{obj.pk}/');client.assert_not_called()
    def test_admin_policy_hard_caps(self):
        self.policy.max_probes=51
        with self.assertRaises(ValidationError):self.policy.save()
        self.policy.max_probes=5;self.policy.probes_per_hour=251
        with self.assertRaises(ValidationError):self.policy.save()
    def test_shared_probe_budget(self):
        self.policy.probes_per_hour=2;self.policy.save();reserve_probes(2,self.policy)
        with self.assertRaises(LimitExceeded):reserve_probes(1,self.policy)
    @patch('globalping.tasks.validate_dns')
    @patch('globalping.tasks.GlobalpingClient')
    @patch('globalping.tasks.poll_measurement.apply_async')
    def test_create_once_and_scheduled_poll(self,poll,client,dns):
        obj=self.obj();client.return_value.create.return_value=APIResponse({'id':'actualRemote1','probesCount':1},202,'',{'consumed':1,'remaining':249})
        create_measurement(str(obj.pk));create_measurement(str(obj.pk));obj.refresh_from_db()
        self.assertEqual(obj.remote_id,'actualRemote1');self.assertEqual(client.return_value.create.call_count,1);self.assertEqual(obj.consumed,1);poll.assert_called_once()
    @patch('globalping.tasks.validate_dns',side_effect=ValueError('Privado'))
    @patch('globalping.tasks.GlobalpingClient')
    def test_worker_dns_block(self,client,dns):
        obj=self.obj();create_measurement(str(obj.pk));client.assert_not_called();obj.refresh_from_db();self.assertEqual(obj.status,'failed')
    @patch('globalping.tasks.validate_dns')
    @patch('globalping.tasks.GlobalpingClient')
    def test_post_timeout_never_retried(self,client,dns):
        client.return_value.create.side_effect=APIError('Timeout')
        obj=self.obj();create_measurement(str(obj.pk));create_measurement(str(obj.pk));self.assertEqual(client.return_value.create.call_count,1)
    @patch('globalping.tasks.GlobalpingClient')
    def test_poll_stores_real_fields_and_stops(self,client):
        obj=self.obj(status='in-progress',remote_id='actualRemote1');client.return_value.get.return_value=APIResponse(PING,200,'"etag"',{})
        poll_measurement(str(obj.pk));obj.refresh_from_db()
        self.assertEqual(obj.status,'finished');self.assertEqual(obj.results['rows'][0]['avg'],1.5)
        poll_measurement(str(obj.pk));self.assertEqual(client.return_value.get.call_count,1)
    @patch('globalping.tasks.validate_dns')
    @patch('globalping.tasks.GlobalpingClient')
    def test_cached_result_avoids_create(self,client,dns):
        obj=self.obj()
        cache.set('gp:result:'+fingerprint(obj.payload),{'remote_id':'actualRemote1','results':normalize(PING,'ping'),'probes_count':1,'measured_at':timezone.now()},300)
        create_measurement(str(obj.pk));obj.refresh_from_db();client.assert_not_called()
        self.assertTrue(obj.from_cache);self.assertEqual(obj.consumed,0)
    @patch('globalping.tasks.GlobalpingClient')
    @patch('globalping.tasks.poll_measurement.apply_async')
    def test_304_retains_partial_and_reschedules(self,poll,client):
        obj=self.obj(status='in-progress',remote_id='actualRemote1',etag='"old"',results={'rows':[]})
        client.return_value.get.return_value=APIResponse({},304,'"old"',{})
        poll_measurement(str(obj.pk));obj.refresh_from_db();self.assertEqual(obj.results,{'rows':[]});self.assertEqual(obj.status,'in-progress');poll.assert_called_once()
    @patch('globalping.tasks.GlobalpingClient')
    @patch('globalping.tasks.poll_measurement.apply_async')
    def test_poll_429_waits(self,poll,client):
        obj=self.obj(status='in-progress',remote_id='actualRemote1');client.return_value.get.side_effect=APIError('limit',429,12)
        poll_measurement(str(obj.pk));self.assertEqual(poll.call_args.kwargs['countdown'],12)
    @patch('globalping.tasks.GlobalpingClient')
    def test_poll_timeout(self,client):
        obj=self.obj(status='in-progress',remote_id='actualRemote1');Measurement.objects.filter(pk=obj.pk).update(created_at=timezone.now()-timedelta(seconds=200))
        poll_measurement(str(obj.pk));client.assert_not_called();obj.refresh_from_db();self.assertEqual(obj.status,'failed')
    @patch('globalping.tasks.GlobalpingClient')
    @patch('globalping.tasks.poll_measurement.apply_async')
    def test_duplicate_poll_throttled(self,poll,client):
        obj=self.obj(status='in-progress',remote_id='actualRemote1');client.return_value.get.return_value=APIResponse({'id':'actualRemote1','type':'ping','status':'in-progress','results':[]},200,'',{})
        poll_measurement(str(obj.pk));poll_measurement(str(obj.pk));self.assertEqual(client.return_value.get.call_count,1)
    def test_retention_and_stalled_cleanup(self):
        obj=self.obj(expires_at=timezone.now()-timedelta(seconds=1));cleanup();self.assertFalse(Measurement.objects.filter(pk=obj.pk).exists())
        obj=self.obj(status='creating');Measurement.objects.filter(pk=obj.pk).update(created_at=timezone.now()-timedelta(seconds=200));expire_stalled();obj.refresh_from_db();self.assertEqual(obj.status,'failed')
    @patch('globalping.views.create_measurement.delay',side_effect=ConnectionError())
    def test_broker_failure_is_reported(self,queue):
        r=self.post();self.assertEqual(r.status_code,503);self.assertEqual(Measurement.objects.get().status,'failed')

class SessionAndErrorTests(TestCase):
    def setUp(self):cache.clear()
    @patch('globalping.views.create_measurement.delay')
    def test_history_survives_login_rotation(self,queue):
        r=self.client.post('/api/globalping/medicoes/',json.dumps(INPUT),content_type='application/json')
        self.assertEqual(r.status_code,202)
        pk=r.json()['id'];user=get_user_model().objects.create_user('new-login')
        self.client.force_login(user)
        self.assertEqual(self.client.get(f'/api/globalping/medicoes/{pk}/').status_code,200)
    def test_api_errors_noindex(self):
        r=self.client.get('/api/globalping/medicoes/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(r.status_code,404);self.assertIn('noindex',r['X-Robots-Tag'])
    @patch('globalping.tasks.validate_dns')
    @patch('globalping.tasks.GlobalpingClient')
    def test_stale_work_cannot_create_remote(self,client,dns):
        obj=Measurement.objects.create(session_hash='s',kind='ping',target='example.com',payload={'limit':1},probes_requested=1,expires_at=timezone.now()+timedelta(hours=1))
        Measurement.objects.filter(pk=obj.pk).update(created_at=timezone.now()-timedelta(seconds=200))
        create_measurement(str(obj.pk));client.assert_not_called()
