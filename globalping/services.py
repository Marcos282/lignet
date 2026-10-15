"""Globalping v1 client. All traffic goes to the fixed official API, anonymously.
No URL from an API Location header or from a visitor is ever fetched here.
"""
import json
import re
from dataclasses import dataclass
import requests
from django.conf import settings

BASE = 'https://api.globalping.io/v1'
ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,128}$')
HEADERS = {'User-Agent':'LignetGlobalPing/1.0 (+https://lignetbrasil.com.br/ferramentas/ping-mundial/)', 'Accept':'application/json', 'Accept-Encoding':'gzip'}


class APIError(Exception):
    def __init__(self,message,status=None,retry_after=None,usage=None):
        super().__init__(message)
        self.status=status
        self.retry_after=retry_after
        self.usage=usage or {}


def integer(value):
    try: return max(0,int(value))
    except (ValueError,TypeError): return None


def usage(headers):
    return {name:integer(headers.get(header)) for name,header in {
        'consumed':'X-RateLimit-Consumed','remaining':'X-RateLimit-Remaining',
        'quota_reset':'X-RateLimit-Reset','quota_limit':'X-RateLimit-Limit',
        'credits_consumed':'X-Credits-Consumed'}.items()}


@dataclass
class APIResponse:
    data: dict
    status: int
    etag: str
    usage: dict


class GlobalpingClient:
    def request(self,method,path,payload=None,etag=''):
        headers=dict(HEADERS)
        if etag: headers['If-None-Match']=etag
        # Ignore environment proxy/netrc credentials. No token, no paid credits.
        try:
            with requests.Session() as session:
                session.trust_env=False
                with session.request(method,BASE+path,json=payload,headers=headers,timeout=(3,10),allow_redirects=False,stream=True) as response:
                    status=response.status_code
                    counters=usage(response.headers)
                    if status==304: return APIResponse({},status,etag,counters)
                    if status==429:
                        retry=integer(response.headers.get('Retry-After')) or counters.get('quota_reset') or 60
                        raise APIError('A cota da Globalping foi atingida. Aguarde antes de iniciar outro teste.',status,min(retry,86400),counters)
                    if status not in (200,202):
                        messages={400:'A API recusou os parâmetros do teste.',404:'Medição não encontrada na Globalping.',422:'Não há sondas disponíveis para este destino ou filtro.'}
                        raise APIError(messages.get(status,'A Globalping está indisponível. Tente novamente mais tarde.'),status,usage=counters)
                    chunks=[]; size=0
                    for chunk in response.iter_content(65536):
                        size+=len(chunk)
                        if size>2*1024*1024: raise APIError('A resposta da Globalping ultrapassou o limite de segurança.')
                        chunks.append(chunk)
                    data=json.loads(b''.join(chunks))
                    if not isinstance(data,dict): raise APIError('Resposta inesperada da Globalping.')
                    return APIResponse(data,status,response.headers.get('ETag','')[:256],counters)
        except APIError: raise
        except (requests.RequestException,ValueError,TypeError) as exc:
            # Never include request headers, URLs with secrets, or upstream bodies in errors.
            raise APIError('Não foi possível consultar a Globalping. O teste não será reenviado automaticamente.') from exc

    def create(self,payload):
        result=self.request('POST','/measurements',payload)
        if result.status!=202 or not ID_PATTERN.fullmatch(str(result.data.get('id',''))) or type(result.data.get('probesCount')) is not int:
            raise APIError('A Globalping não retornou um identificador de medição válido.')
        if not 0<=result.data['probesCount']<=payload['limit']: raise APIError('Quantidade de sondas inesperada.')
        return result

    def get(self,remote_id,etag=''):
        if not ID_PATTERN.fullmatch(remote_id): raise APIError('Identificador de medição inválido.')
        return self.request('GET','/measurements/'+remote_id,etag=etag)
