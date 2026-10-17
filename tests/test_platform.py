import ipaddress
import socket
from unittest.mock import patch,MagicMock
from xml.etree.ElementTree import fromstring
from django.test import TestCase,SimpleTestCase,override_settings,Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from core.network import normalize_url,public_addresses,UnsafeURL,fetch,Response,PinnedHTTP,PinnedHTTPS
from seo_audit.services import inspect_html,audit,WEIGHTS
from seo_audit.models import SeoAudit
from seo_audit.tasks import run_audit
from accounts.models import Domain,DomainVerification
from accounts.services import verify
from indexnow.models import IndexNowSubmission
from indexnow.tasks import submit
from sitemaps.services import generate
from robots_tools.services import generate as robots

HTML=b'''<html><head><title>Uma pagina de teste completa para auditoria SEO</title><meta name="description" content="Uma descricao editorial suficientemente longa para explicar o conteudo desta pagina de teste e orientar o visitante."><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="canonical" href="https://example.com/"><meta property="og:title" content="Teste"><meta property="og:description" content="Descricao"><meta property="og:image" content="https://example.com/a.png"><meta name="twitter:card" content="summary"><script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage"}</script></head><body><h1>Teste</h1><h2>Conteudo</h2><img src="x" alt=""><a href="/contato">Contato</a></body></html>'''
def response(body=HTML,status=200,url='https://example.com/',headers=None):
    return Response(url,status,headers or {'content-type':'text/html'},body,[],0.1)

class URLTests(SimpleTestCase):
    def test_bad_inputs(self):
        for url in ['file:///etc/passwd','ftp://example.com','http://127.0.0.1','http://10.0.0.1','http://169.254.169.254','http://[::1]','http://[::ffff:8.8.8.8]','http://224.0.0.1','https://a:pass@example.com','http://example.com:22','http://example.com\\@127.0.0.1','http://example.com/\r\nx','http://[fe80::1%eth0]']:
            with self.subTest(url=url),self.assertRaises(ValueError): normalize_url(url)
    def test_normalize(self):
        self.assertEqual(normalize_url('HTTPS://Example.COM/a#x'),'https://example.com/a')
    @patch('core.network.socket.getaddrinfo')
    def test_mixed_dns_denied(self,dns):
        dns.return_value=[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('10.1.1.1',443))]
        with self.assertRaises(UnsafeURL): public_addresses('example.com',443)
    @patch('core.network.socket.getaddrinfo')
    def test_public_dns(self,dns):
        dns.return_value=[(2,1,6,'',('8.8.8.8',443))]
        self.assertEqual(len(public_addresses('example.com',443)),1)
    @patch('core.network.socket.socket')
    def test_connect_uses_pinned_address(self,sock):
        sock.return_value.getpeername.return_value=('8.8.8.8',80)
        conn=PinnedHTTP('example.com',80,(2,1,6,'',('8.8.8.8',80)),2)
        conn.connect(); sock.return_value.connect.assert_called_once_with(('8.8.8.8',80))
    @patch('core.network.socket.socket')
    def test_peer_mismatch_rejected(self,sock):
        sock.return_value.getpeername.return_value=('127.0.0.1',80)
        with self.assertRaises(UnsafeURL): PinnedHTTP('example.com',80,(2,1,6,'',('8.8.8.8',80)),2).connect()

class NetworkTests(TestCase):
    @patch('core.network.PinnedHTTPS')
    @patch('core.network.public_addresses')
    def test_private_redirect_blocked(self,dns,conn):
        dns.return_value=[(2,1,6,'',('8.8.8.8',443))]
        r=conn.return_value.getresponse.return_value;r.status=302;r.getheaders.return_value=[('location','http://127.0.0.1/')]
        with self.assertRaises(UnsafeURL): fetch('https://example.com')
        self.assertEqual(conn.call_count,1)
    @patch('core.network.PinnedHTTPS')
    @patch('core.network.public_addresses')
    def test_dns_revalidated_per_redirect(self,dns,conn):
        dns.side_effect=[[(2,1,6,'',('8.8.8.8',443))],UnsafeURL('rebound')]
        r=conn.return_value.getresponse.return_value;r.status=302;r.getheaders.return_value=[('location','/next')]
        with self.assertRaises(UnsafeURL): fetch('https://example.com')
        self.assertEqual(dns.call_count,2)
    @override_settings(MAX_RESPONSE_BYTES=10)
    @patch('core.network.PinnedHTTPS')
    @patch('core.network.public_addresses')
    def test_size_limit(self,dns,conn):
        dns.return_value=[(2,1,6,'',('8.8.8.8',443))]
        r=conn.return_value.getresponse.return_value;r.status=200;r.getheaders.return_value=[('content-length','11')]
        with self.assertRaises(UnsafeURL): fetch('https://example.com')
    def test_blocked_host(self):
        from core.models import BlockedHost
        BlockedHost.objects.create(hostname='example.com',reason='test')
        with patch('core.network.public_addresses') as dns:
            with self.assertRaises(UnsafeURL): fetch('https://example.com')
            dns.assert_not_called()

class GeneratorTests(SimpleTestCase):
    def test_xml_escaped_deduplicated(self):
        xml,n=generate('https://example.com/?a=1&b=2\nhttps://example.com/?a=1&b=2')
        self.assertEqual(n,1); self.assertIn(b'&amp;',xml); self.assertEqual(len(fromstring(xml)),1)
    def test_mixed_host_denied(self):
        with self.assertRaises(ValueError): generate('https://example.com\nhttps://other.com')
    def test_empty_denied(self):
        with self.assertRaises(ValueError): generate('')
    def test_protocol_limit(self):
        with self.assertRaises(ValueError): generate('https://example.com\n'*50001)
    def test_robots(self):
        text=robots('*\nBingbot','/','/admin/','https://example.com/sitemap.xml')
        self.assertIn('User-agent: Bingbot',text); self.assertIn('Disallow: /admin/',text)
    def test_robots_injection(self):
        with self.assertRaises(ValueError): robots('*\nSitemap: bad','/','','')
        with self.assertRaises(ValueError): robots('*','','x','')

class AuditTests(TestCase):
    def test_html_signals(self):
        data=inspect_html(response());self.assertEqual(data['missing_alt'],0);self.assertTrue(all(data['checks'].values())); self.assertEqual(sum(WEIGHTS.values()),100)
    def test_header_noindex(self):
        self.assertFalse(inspect_html(response(headers={'x-robots-tag':'noindex'}))['checks']['indexable'])
    def test_heading_skip(self):
        self.assertFalse(inspect_html(response(HTML.replace(b'<h2>',b'<h3>').replace(b'</h2>',b'</h3>')))['checks']['headings'])
    @patch('seo_audit.services.fetch')
    def test_audit_and_files(self,fetch_mock):
        fetch_mock.side_effect=[response(),response(b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>'),response(b'User-agent: *\nAllow: /'),response(status=404)]
        result=audit('https://example.com')
        self.assertEqual(result['score'],100);self.assertEqual(len(result['broken_links']),1)
    @patch('seo_audit.tasks.audit')
    def test_task_failure_and_idempotency(self,work):
        obj=SeoAudit.objects.create(url='https://example.com')
        work.side_effect=ValueError('private internal detail')
        run_audit(str(obj.pk));run_audit(str(obj.pk));obj.refresh_from_db()
        self.assertEqual(obj.status,'failed');self.assertNotIn('private',obj.error);self.assertEqual(work.call_count,1)
    @patch('seo_audit.tasks.audit')
    def test_task_persists_issue(self,work):
        obj=SeoAudit.objects.create(url='https://example.com')
        work.return_value={'checks':{'title':False},'score':90,'broken_links':[]}
        run_audit(str(obj.pk));obj.refresh_from_db()
        self.assertEqual(obj.score,90);self.assertEqual(obj.issues.count(),1)

class PermissionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=get_user_model().objects.create_user('owner',password='example-password-long')
        self.other=get_user_model().objects.create_user('other',password='another-password-long')
        self.domain=Domain.objects.create(owner=self.user,hostname='example.com',status='verified')
        DomainVerification.objects.create(domain=self.domain)
    def test_public_pages(self):
        for path in ['/','/ferramentas/seo/','/ferramentas/sitemap/','/ferramentas/robots-txt/','/ferramentas/indexnow/','/ferramentas/consultar-dns/','/ferramentas/calculadora-cidr/','/sitemap.xml','/robots.txt','/qr.js','/vendor/qrcode.js','/conta/login/','/conta/cadastro/']:
            with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
    @override_settings(GA4_MEASUREMENT_ID='G-ZR765MQK3B')
    def test_ga4_is_included_once_in_base_template(self):
        for path in ['/ferramentas/seo/','/ferramentas/sitemap/','/conta/login/']:
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.content.count(b'googletagmanager.com/gtag/js'),1)
                self.assertEqual(response.content.count(b"gtag('config', 'G-ZR765MQK3B')"),1)
    @override_settings(GA4_MEASUREMENT_ID='G-ENVTEST123')
    def test_ga4_uses_environment_id_on_homepage(self):
        response=self.client.get('/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content.count(b'googletagmanager.com/gtag/js'),1)
        self.assertIn(b"gtag('config', 'G-ENVTEST123')",response.content)
        self.assertIn(b'G-ENVTEST123',response.content)
        self.assertNotIn(b'G-ZR765MQK3B',response.content)
    @override_settings(GA4_MEASUREMENT_ID='')
    def test_ga4_can_be_disabled_without_emitting_an_empty_tag(self):
        for path in ['/ferramentas/seo/','/']:
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                self.assertNotContains(response,'googletagmanager.com/gtag/js')
    def test_dashboard_requires_login(self): self.assertEqual(self.client.get('/painel/').status_code,302)
    def test_dashboard_render(self):
        self.client.force_login(self.user);self.assertContains(self.client.get('/painel/'),'example.com')
    def test_owner_only(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/dominios/{self.domain.pk}/key/').status_code,404)
    def test_report_session_private(self):
        obj=SeoAudit.objects.create(url='https://example.com')
        self.assertEqual(self.client.get(f'/relatorios/{obj.pk}/').status_code,404)
        session=self.client.session;session['audit_ids']=[str(obj.pk)];session.save()
        r=self.client.get(f'/relatorios/{obj.pk}/');self.assertEqual(r.status_code,200);self.assertEqual(r['Cache-Control'],'private, no-store');self.assertIn('noindex',r['X-Robots-Tag'])
    def test_report_owner_private(self):
        obj=SeoAudit.objects.create(url='https://example.com',owner=self.user)
        self.client.force_login(self.other);self.assertEqual(self.client.get(f'/relatorios/{obj.pk}/').status_code,404)
        self.client.force_login(self.user);self.assertEqual(self.client.get(f'/relatorios/{obj.pk}/').status_code,200)
    def test_csrf(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/ferramentas/seo/',{'url':'https://example.com'}).status_code,403)
    @override_settings(AUDIT_HOURLY_LIMIT=1)
    @patch('core.views.run_audit.delay')
    def test_rate_limit_and_queue(self,queue):
        r=self.client.post('/ferramentas/seo/',{'url':'https://example.com'})
        self.assertEqual(r.status_code,302);queue.assert_called_once()
        self.assertEqual(self.client.post('/ferramentas/seo/',{'url':'https://example.com'}).status_code,429)
    @override_settings(MAX_DOMAINS=1)
    def test_domain_limit(self):
        self.client.force_login(self.user)
        r=self.client.post('/painel/',{'hostname':'new.example.com'})
        self.assertContains(r,'Limite de domínios');self.assertEqual(Domain.objects.filter(owner=self.user).count(),1)
    @patch('accounts.services.fetch')
    def test_domain_verification(self,get):
        get.return_value=response(self.domain.verification.key.encode());self.assertTrue(verify(self.domain))
        get.return_value=response(b'wrong');self.assertFalse(verify(self.domain));self.domain.refresh_from_db();self.assertEqual(self.domain.status,'pending')
    @patch('indexnow.tasks.verify')
    @patch('indexnow.tasks.requests.post')
    def test_indexnow_revalidates(self,post,check):
        check.return_value=False
        obj=IndexNowSubmission.objects.create(owner=self.user,domain=self.domain,urls=['https://example.com/'])
        submit(obj.pk);post.assert_not_called();obj.refresh_from_db();self.assertEqual(obj.status,'failed')
    @patch('indexnow.tasks.verify',return_value=True)
    @patch('indexnow.tasks.requests.post')
    def test_indexnow_wrong_host(self,post,check):
        obj=IndexNowSubmission.objects.create(owner=self.user,domain=self.domain,urls=['https://other.com/'])
        submit(obj.pk);post.assert_not_called()
    @patch('indexnow.tasks.verify',return_value=True)
    @patch('indexnow.tasks.requests.post')
    def test_indexnow_api_and_idempotency(self,post,check):
        post.return_value.status_code=202
        obj=IndexNowSubmission.objects.create(owner=self.user,domain=self.domain,urls=['https://example.com/'])
        submit(obj.pk);submit(obj.pk);obj.refresh_from_db()
        self.assertEqual(obj.status,'validation_pending');self.assertEqual(post.call_count,1)
    @patch('core.views.submit.delay')
    def test_indexnow_frequency(self,queue):
        self.client.force_login(self.user)
        for _ in range(2): self.client.post(f'/dominios/{self.domain.pk}/indexnow/',{'urls':'https://example.com/'})
        self.assertEqual(IndexNowSubmission.objects.count(),1);self.assertEqual(queue.call_count,1)
    def test_oauth_state(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/integracoes/google/callback/?state=bad&code=x').status_code,400)
    def test_oauth_requires_verified_owner(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f'/integracoes/google/{self.domain.pk}/conectar/').status_code,404)

class IntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=get_user_model().objects.create_user('integration-owner')
        self.domain=Domain.objects.create(owner=self.user,hostname='example.com',status='verified',monitoring_enabled=True)
        DomainVerification.objects.create(domain=self.domain)
    def test_google_encryption(self):
        import json
        from cryptography.fernet import Fernet
        from search_console.models import SearchConsoleConnection
        from search_console.services import save_tokens,token
        obj=SearchConsoleConnection.objects.create(domain=self.domain,owner=self.user,property_url='sc-domain:example.com')
        key=Fernet.generate_key().decode()
        with override_settings(TOKEN_ENCRYPTION_KEY=key):
            save_tokens(obj,{'access_token':'sensitive-value','refresh_token':'refresh-value','expires_in':3600})
            self.assertNotIn('sensitive-value',obj.encrypted_tokens)
            self.assertEqual(token(obj),'sensitive-value')
    @patch('search_console.services.requests.post')
    def test_google_refresh_preserves_refresh_token(self,post):
        from cryptography.fernet import Fernet
        from search_console.models import SearchConsoleConnection
        from search_console.services import save_tokens,token,cipher
        import json
        obj=SearchConsoleConnection.objects.create(domain=self.domain,owner=self.user,property_url='sc-domain:example.com')
        with override_settings(TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode()):
            save_tokens(obj,{'access_token':'old','refresh_token':'keep','expires_in':-1})
            post.return_value.json.return_value={'access_token':'new','expires_in':3600}
            self.assertEqual(token(obj),'new')
            self.assertEqual(json.loads(cipher().decrypt(obj.encrypted_tokens.encode()))['refresh_token'],'keep')
    @patch('search_console.tasks.collect')
    @patch('search_console.tasks.verify',return_value=True)
    def test_search_console_sync(self,verify_mock,collect_mock):
        from search_console.models import SearchConsoleConnection
        from search_console.tasks import sync
        obj=SearchConsoleConnection.objects.create(domain=self.domain,owner=self.user,property_url='sc-domain:example.com')
        sync(obj.pk);collect_mock.assert_called_once();obj.refresh_from_db();self.assertEqual(obj.status,'connected')
    @patch('search_console.services.api')
    def test_google_official_operations(self,api):
        from search_console.models import SearchConsoleConnection
        from search_console.services import collect
        obj=SearchConsoleConnection.objects.create(domain=self.domain,owner=self.user,property_url='sc-domain:example.com')
        api.side_effect=[{'rows':[{'clicks':10,'impressions':100,'ctr':0.1,'position':5}]},{'sitemap':[]},{'inspectionResult':{'indexStatusResult':{'verdict':'PASS'}}}]
        collect(obj);obj.refresh_from_db()
        self.assertEqual(obj.data['analytics']['rows'][0]['clicks'],10)
        self.assertIn('urlInspection/index:inspect',api.call_args.args)
    @override_settings(GOOGLE_CLIENT_ID='client',GOOGLE_CLIENT_SECRET='secret')
    @patch('search_console.views.requests.get')
    @patch('search_console.views.requests.post')
    def test_google_oauth_success_and_replay(self,post,get):
        from cryptography.fernet import Fernet
        from search_console.models import SearchConsoleConnection
        self.client.force_login(self.user)
        with override_settings(TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode()):
            r=self.client.post(f'/integracoes/google/{self.domain.pk}/conectar/')
            self.assertEqual(r.status_code,302);self.assertIn('code_challenge=',r.url)
            state=self.client.session['google_oauth']['state']
            post.return_value.json.return_value={'access_token':'token','refresh_token':'refresh','expires_in':3600}
            get.return_value.json.return_value={'siteEntry':[{'siteUrl':'sc-domain:example.com','permissionLevel':'siteOwner'}]}
            self.assertEqual(self.client.get('/integracoes/google/callback/',{'state':state,'code':'authorization'}).status_code,302)
            self.assertEqual(SearchConsoleConnection.objects.count(),1)
            self.assertEqual(self.client.get('/integracoes/google/callback/',{'state':state,'code':'authorization'}).status_code,400)
    @patch('monitoring.tasks.run_check.delay')
    def test_monitor_scheduler_deduplicates(self,queue):
        from monitoring.tasks import schedule_checks
        from monitoring.models import MonitoringCheck
        with self.captureOnCommitCallbacks(execute=True): schedule_checks();schedule_checks()
        self.assertEqual(MonitoringCheck.objects.count(),1);queue.assert_called_once()
    @patch('monitoring.tasks.audit')
    @patch('monitoring.tasks.verify',return_value=True)
    def test_monitor_metadata_changes(self,verify_mock,audit_mock):
        from monitoring.models import MonitoringCheck
        from monitoring.tasks import run_check
        MonitoringCheck.objects.create(domain=self.domain,status='complete',report={'title':'before','description':'same','robots_directives':''})
        obj=MonitoringCheck.objects.create(domain=self.domain)
        audit_mock.return_value={'title':'after','description':'same','robots_directives':'','checks':{'http':True,'https':True,'sitemap':False,'indexable':True}}
        run_check(obj.pk);obj.refresh_from_db()
        self.assertEqual(obj.status,'complete');self.assertIn('Alteração detectada: title',obj.alerts);self.assertIn('Revisar: sitemap',obj.alerts)
    @patch('monitoring.tasks.audit')
    @patch('monitoring.tasks.verify',return_value=False)
    def test_monitor_denies_unverified(self,verify_mock,audit_mock):
        from monitoring.models import MonitoringCheck
        from monitoring.tasks import run_check
        obj=MonitoringCheck.objects.create(domain=self.domain)
        run_check(obj.pk);audit_mock.assert_not_called();obj.refresh_from_db();self.assertEqual(obj.status,'failed')

class ProxyAndAdminTests(TestCase):
    def test_untrusted_header_ignored(self):
        from core.middleware import TrustedProxyIPMiddleware
        from django.test import RequestFactory
        request=RequestFactory().get('/',REMOTE_ADDR='8.8.8.8',HTTP_X_REAL_IP='1.1.1.1')
        TrustedProxyIPMiddleware(lambda r:r)(request)
        self.assertEqual(request.META['REMOTE_ADDR'],'8.8.8.8')
    @override_settings(TRUSTED_PROXY_IPS=['127.0.0.1'])
    def test_trusted_proxy_exact_ip(self):
        from core.middleware import TrustedProxyIPMiddleware
        from django.test import RequestFactory
        request=RequestFactory().get('/',REMOTE_ADDR='127.0.0.1',HTTP_X_REAL_IP='1.1.1.1')
        TrustedProxyIPMiddleware(lambda r:r)(request)
        self.assertEqual(request.META['REMOTE_ADDR'],'1.1.1.1')
    def test_operations_staff_only(self):
        self.assertEqual(self.client.get('/admin/operacao/').status_code,302)
        user=get_user_model().objects.create_user('staff',is_staff=True)
        self.client.force_login(user)
        self.assertContains(self.client.get('/admin/operacao/'),'Atividade da aplicação')
