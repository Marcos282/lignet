from celery import shared_task
from urllib.parse import quote,urlsplit
from .models import SearchConsoleConnection
from .services import collect,api,property_path
from accounts.services import verify
from core.network import normalize_url
from core.security import record

@shared_task
def sync(connection_id,sitemap=''):
    connection=SearchConsoleConnection.objects.select_related('domain').get(pk=connection_id)
    try:
        if connection.owner_id!=connection.domain.owner_id or not verify(connection.domain): raise ValueError('Domínio não verificado')
        if sitemap:
            sitemap=normalize_url(sitemap)
            if urlsplit(sitemap).hostname!=connection.domain.hostname: raise ValueError('Sitemap de outro domínio')
            api(connection,'PUT',property_path(connection)+'/sitemaps/'+quote(sitemap,safe=''))
        collect(connection); connection.status='connected'
    except Exception: connection.status='error'
    connection.save(); record('search_console',connection.status,connection.owner,connection.pk)
