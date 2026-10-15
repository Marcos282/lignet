import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps
from core.models import Activity

logger=logging.getLogger('lignet.audit')
def record(event,status,owner=None,object_id=''):
    Activity.objects.create(event=event,status=status,owner=owner if owner and owner.is_authenticated else None,object_id=str(object_id))
    logger.info('%s status=%s object=%s',event,status,object_id)

def limited(limit_setting='ACTION_HOURLY_LIMIT'):
    def decorate(view):
        @wraps(view)
        def wrapped(request,*args,**kwargs):
            if request.method=='POST':
                # Never trust client-controlled X-Forwarded-For. Configure real_ip in Nginx.
                identities=['ip:'+request.META.get('REMOTE_ADDR','unknown')]
                if request.user.is_authenticated: identities.append('user:'+str(request.user.pk))
                for identity in identities:
                    key='limit:'+hashlib.sha256((limit_setting+identity).encode()).hexdigest()
                    cache.add(key,0,3600)
                    count=cache.incr(key)
                    if count>getattr(settings,limit_setting):
                        response=HttpResponse('Limite de uso atingido. Tente novamente em uma hora.',status=429)
                        response['Retry-After']='3600'
                        return response
            return view(request,*args,**kwargs)
        return wrapped
    return decorate
