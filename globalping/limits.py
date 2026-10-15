import hashlib
import json
from django.core.cache import cache
from django.utils import timezone


class LimitExceeded(Exception):
    def __init__(self,message,retry_after=3600):
        super().__init__(message)
        self.retry_after=retry_after


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def increment(key,cost,limit,ttl=3600):
    cache.add(key,0,ttl)
    # django-redis backend's incr is atomic; never implement a read/modify/write.
    value=cache.incr(key,cost)
    if value>limit: raise LimitExceeded('Limite de uso atingido. Aguarde para iniciar outro teste.',ttl)


def limit_request(request,limit,category):
    identities=['ip:'+request.META.get('REMOTE_ADDR','unknown')]
    if request.user.is_authenticated: identities.append('user:'+str(request.user.pk))
    for identity in identities:
        digest=hashlib.sha256(identity.encode()).hexdigest()
        increment('gp:'+category+':'+digest,1,limit)


def reserve_probes(count,policy):
    wait=cache.get('gp:provider:backoff')
    if wait and wait>timezone.now().timestamp():
        raise LimitExceeded('A Globalping atingiu a cota compartilhada. Tente novamente mais tarde.',max(1,int(wait-timezone.now().timestamp())))
    # Never exceed the official anonymous cap, even with stale/invalid DB settings.
    increment('gp:budget:probes',count,min(policy.probes_per_hour,250))


def backoff(seconds):
    seconds=max(1,min(seconds or 60,86400))
    cache.set('gp:provider:backoff',timezone.now().timestamp()+seconds,seconds)
