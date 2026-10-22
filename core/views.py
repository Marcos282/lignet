from pathlib import Path
from urllib.parse import urlsplit
import ipaddress
import socket
from django.conf import settings
from django.http import HttpResponse,FileResponse
from django.template.loader import render_to_string
from .portal_navigation import replace_navigation
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import transaction,IntegrityError
from django.utils import timezone
from .forms import AuditForm,SitemapForm,RobotsForm,DomainForm
from .security import limited,record
from seo_audit.models import SeoAudit
from seo_audit.tasks import run_audit
from accounts.models import Domain,DomainVerification
from accounts.tasks import verify_domain
from indexnow.models import IndexNowSubmission
from indexnow.tasks import submit

META={
'seo':('Analisador SEO gratuito','Encontre problemas de SEO, entenda sua pontuação e descubra como melhorar sua página.'),
'sitemap':('Gerador de sitemap XML','Crie um sitemap XML válido com suas URLs, remova duplicatas e baixe gratuitamente.'),
'robots-txt':('Gerador de robots.txt','Configure regras para robôs de busca e baixe um robots.txt para seu domínio.'),
'indexnow':('Notifique URLs com IndexNow','Verifique seu domínio e informe URLs atualizadas aos mecanismos participantes do IndexNow.'),
'consultar-dns':('Consultar DNS','Consulte os endereços públicos IPv4 e IPv6 de um domínio.'),
'calculadora-cidr':('Calculadora CIDR','Calcule redes IPv4 e IPv6, máscaras e intervalos de endereços.')}

def portal(request):
    html=(settings.BASE_DIR/'index.html').read_text(encoding='utf-8')
    html=replace_navigation(html,render_to_string('includes/navigation.html',request=request))
    start_marker='<!-- GA4_TAG_START -->'
    end_marker='<!-- GA4_TAG_END -->'
    start=html.index(start_marker)
    end=html.index(end_marker,start)+len(end_marker)
    tag=''
    if settings.GA4_MEASUREMENT_ID:
        measurement_id=settings.GA4_MEASUREMENT_ID
        tag=f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}');
</script>'''
    html=html[:start]+tag+html[end:]
    return HttpResponse(html,content_type='text/html')

def legacy_asset(request,name):
    allowed={'qr.js':'application/javascript','vendor/qrcode.js':'application/javascript','vendor/qrcode_UTF8.js':'application/javascript'}
    if name not in allowed:
        from django.http import Http404
        raise Http404
    return FileResponse(open(settings.BASE_DIR/name,'rb'),content_type=allowed[name])

@limited('AUDIT_HOURLY_LIMIT')
def seo(request):
    form=AuditForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        owner=request.user if request.user.is_authenticated else None
        obj=SeoAudit.objects.create(url=form.cleaned_data['url'],owner=owner)
        ids=request.session.get('audit_ids',[]); request.session['audit_ids']=(ids+[str(obj.pk)])[-30:]
        try: run_audit.delay(str(obj.pk))
        except Exception:
            obj.status='failed'; obj.error='Fila indisponível. Tente mais tarde.'; obj.save()
        record('audit_requested',obj.status,owner,obj.pk)
        return redirect('report',pk=obj.pk)
    return render(request,'tool.html',{'kind':'seo','form':form,'title':META['seo'][0],'description':META['seo'][1]})

def report(request,pk):
    query=SeoAudit.objects.filter(pk=pk)
    if request.user.is_authenticated: obj=query.filter(owner=request.user).first()
    else: obj=None
    if obj is None and str(pk) in request.session.get('audit_ids',[]): obj=query.first()
    if obj is None:
        from django.http import Http404
        raise Http404
    from django.db.models import Case,When,IntegerField
    issues=obj.issues.order_by(Case(When(severity='critical',then=0),When(severity='attention',then=1),default=2,output_field=IntegerField()),'created_at')
    return render(request,'report.html',{'issues':issues,'audit':obj,'title':'Relatório SEO privado','description':'Resultado da sua auditoria SEO.'})

@limited()
def tool(request,kind):
    title,description=META[kind]; output=None
    form_class={'sitemap':SitemapForm,'robots-txt':RobotsForm,'consultar-dns':DomainForm}.get(kind)
    form=form_class(request.POST or None) if form_class else None
    if request.method=='POST':
        try:
            if kind=='sitemap' and form.is_valid():
                from sitemaps.services import generate
                xml,count=generate(form.cleaned_data['urls'])
                if request.user.is_authenticated:
                    from sitemaps.models import SitemapGeneration
                    SitemapGeneration.objects.create(owner=request.user,url_count=count)
                return download(xml,'sitemap.xml','application/xml')
            if kind=='robots-txt' and form.is_valid():
                from robots_tools.services import generate
                output=generate(**form.cleaned_data)
                if request.POST.get('download'): return download(output,'robots.txt','text/plain; charset=utf-8')
            if kind=='consultar-dns' and form.is_valid():
                from core.network import public_addresses
                # DNS lookup only: no connection or recursive scan.
                output='\n'.join(sorted({a[4][0] for a in public_addresses(form.cleaned_data['hostname'],443)}))
            if kind=='calculadora-cidr':
                network=ipaddress.ip_network(request.POST.get('network',''),strict=False)
                output=f'Rede: {network}\nMáscara: {network.netmask}\nPrimeiro endereço: {network.network_address}\nÚltimo endereço: {network.broadcast_address}\nTotal de endereços: {network.num_addresses}'
        except (ValueError,socket.gaierror) as exc:
            if form: form.add_error(None,str(exc))
            else: messages.error(request,'Rede inválida. Use, por exemplo, 192.168.1.0/24.')
    return render(request,'tool.html',{'kind':kind,'title':title,'description':description,'form':form,'output':output})

def download(body,name,content_type):
    response=HttpResponse(body,content_type=content_type)
    response['Content-Disposition']=f'attachment; filename="{name}"'
    return response

@limited()
def signup(request):
    form=UserCreationForm(request.POST or None)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('login')
    return render(request,'registration/signup.html',{'form':form,'title':'Criar conta gratuita'})

@login_required
@limited()
def dashboard(request):
    form=DomainForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            # Serialize domain-limit enforcement per account.
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if Domain.objects.filter(owner=request.user).count()>=settings.MAX_DOMAINS: form.add_error(None,'Limite de domínios atingido.')
            else:
                domain,created=Domain.objects.get_or_create(owner=request.user,hostname=form.cleaned_data['hostname'])
                if created: DomainVerification.objects.create(domain=domain)
                return redirect('dashboard')
    from monitoring.models import MonitoringCheck
    return render(request,'dashboard.html',{'title':'Meu painel','form':form,'domains':Domain.objects.filter(owner=request.user).select_related('verification'),'audits':SeoAudit.objects.filter(owner=request.user).order_by('-created_at')[:20],'submissions':IndexNowSubmission.objects.filter(owner=request.user).order_by('-created_at')[:30],'checks':MonitoringCheck.objects.filter(domain__owner=request.user).order_by('-created_at')[:20]})

@login_required
@require_POST
@limited()
def domain_action(request,pk,action):
    domain=get_object_or_404(Domain,pk=pk,owner=request.user)
    if action=='key': return download(domain.verification.key,domain.verification.key+'.txt','text/plain')
    if action=='verify':
        try: verify_domain.delay(domain.pk); messages.info(request,'Verificação enviada à fila. Atualize o painel em alguns instantes.')
        except Exception: messages.error(request,'Fila indisponível.')
    elif action=='monitor':
        if domain.status!='verified': messages.error(request,'Verifique a propriedade primeiro.')
        else: domain.monitoring_enabled=not domain.monitoring_enabled; domain.save()
    elif action=='indexnow':
        try:
            from core.network import normalize_url
            urls=list(dict.fromkeys(normalize_url(u.strip()) for u in request.POST.get('urls','').splitlines() if u.strip()))
            if not urls or len(urls)>10000 or any(urlsplit(u).hostname!=domain.hostname for u in urls): raise ValueError('Use de 1 a 10.000 URLs deste domínio.')
            with transaction.atomic():
                domain=Domain.objects.select_for_update().get(pk=domain.pk)
                if domain.status!='verified': raise ValueError('Verifique a propriedade primeiro.')
                if domain.last_indexnow_at and (timezone.now()-domain.last_indexnow_at).total_seconds()<settings.INDEXNOW_COOLDOWN_SECONDS: raise ValueError('Aguarde o intervalo entre envios.')
                obj=IndexNowSubmission.objects.create(owner=request.user,domain=domain,urls=urls)
                domain.last_indexnow_at=timezone.now(); domain.save()
            try: submit.delay(obj.pk)
            except Exception: obj.status='failed'; obj.response_detail='Fila indisponível.'; obj.save(); raise ValueError('Fila indisponível.')
            messages.success(request,'URLs enviadas à fila. O envio não garante indexação.')
        except ValueError as exc: messages.error(request,str(exc))
    return redirect('dashboard')

def portal_sitemap(request):
    from sitemaps.services import generate
    from globalping.views import PAGES
    xml,_=generate('\n'.join([settings.SITE_URL+'/',settings.SITE_URL+'/blog/',settings.SITE_URL+'/ferramentas/simulador-ftth/',settings.SITE_URL+'/ferramentas/projetista-ftth/']+[settings.SITE_URL+'/ferramentas/'+key+'/' for key in list(META)+list(PAGES)]))
    return HttpResponse(xml,content_type='application/xml')

def portal_robots(request):
    return HttpResponse('User-agent: *\nAllow: /\nDisallow: /painel/\nDisallow: /relatorios/\nDisallow: /conta/\nDisallow: /dominios/\nDisallow: /integracoes/\nDisallow: /admin/\nSitemap: '+settings.SITE_URL+'/sitemap.xml\nSitemap: '+settings.SITE_URL+'/blog/sitemap.xml\n',content_type='text/plain')

def operations(request):
    from core.models import Activity
    from monitoring.models import MonitoringCheck
    from django.contrib import admin
    import resource
    from django.db.models import Sum
    from globalping.models import Measurement as GlobalMeasurement
    counts={
        'Análises':SeoAudit.objects.count(),
        'Análises pendentes':SeoAudit.objects.filter(status='pending').count(),
        'Análises em execução':SeoAudit.objects.filter(status='running').count(),
        'Análises concluídas':SeoAudit.objects.filter(status='complete').count(),
        'Falhas de auditoria':SeoAudit.objects.filter(status='failed').count(),
        'Domínios':Domain.objects.count(),
        'Usuários ativos':get_user_model().objects.filter(is_active=True).count(),
        'Notificações IndexNow pendentes':IndexNowSubmission.objects.filter(status='pending').count(),
        'Falhas de monitoramento':MonitoringCheck.objects.filter(status='failed').count(),
        'Medições Global Ping':GlobalMeasurement.objects.count(),
        'Sondas consumidas Global Ping':GlobalMeasurement.objects.aggregate(total=Sum('consumed'))['total'] or 0,
        'Falhas Global Ping':GlobalMeasurement.objects.filter(status='failed').count(),
        'Erros de integração':Activity.objects.filter(event__in=['indexnow','oauth_connected','search_console'],status__in=['failed','error']).count(),
    }
    usage=resource.getrusage(resource.RUSAGE_SELF)
    return render(request,'admin/operations.html',{**admin.site.each_context(request),'title':'Operação Lignet SEO','counts':counts,'process_memory_kb':usage.ru_maxrss,'process_cpu_seconds':round(usage.ru_utime+usage.ru_stime,2),'activities':Activity.objects.order_by('-created_at')[:50]})


def ftth(request):
    return render(request,'ftth.html',{'title':'Simulador FTTH — planejamento visual GPON','description':'Monte uma topologia FTTH, configure perdas e simule potência óptica downstream e upstream gratuitamente no navegador.'})
