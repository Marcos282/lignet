import json
import time
from urllib.parse import quote
import requests
from cryptography.fernet import Fernet
from django.conf import settings

def cipher():
    if not settings.TOKEN_ENCRYPTION_KEY: raise ValueError('Configure TOKEN_ENCRYPTION_KEY.')
    return Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())

def save_tokens(connection,tokens):
    tokens['expires_at']=time.time()+tokens.get('expires_in',3600)-60
    connection.encrypted_tokens=cipher().encrypt(json.dumps(tokens).encode()).decode()
    connection.save()

def token(connection):
    tokens=json.loads(cipher().decrypt(connection.encrypted_tokens.encode()))
    if time.time()>=tokens.get('expires_at',0):
        response=requests.post('https://oauth2.googleapis.com/token',data={'client_id':settings.GOOGLE_CLIENT_ID,'client_secret':settings.GOOGLE_CLIENT_SECRET,'refresh_token':tokens['refresh_token'],'grant_type':'refresh_token'},timeout=15,allow_redirects=False)
        response.raise_for_status(); tokens.update(response.json()); save_tokens(connection,tokens)
    return tokens['access_token']

def api(connection,method,path,body=None,inspection=False):
    base='https://searchconsole.googleapis.com/v1/' if inspection else 'https://www.googleapis.com/webmasters/v3/'
    response=requests.request(method,base+path,headers={'Authorization':'Bearer '+token(connection)},json=body,timeout=20,allow_redirects=False)
    response.raise_for_status()
    return response.json() if response.content else {}

def property_path(connection): return 'sites/'+quote(connection.property_url,safe='')

def collect(connection):
    from datetime import date,timedelta
    end=date.today()-timedelta(days=3); start=end-timedelta(days=27)
    analytics=api(connection,'POST',property_path(connection)+'/searchAnalytics/query',{'startDate':start.isoformat(),'endDate':end.isoformat(),'rowLimit':1})
    sitemaps=api(connection,'GET',property_path(connection)+'/sitemaps')
    inspection=api(connection,'POST','urlInspection/index:inspect',{'inspectionUrl':'https://'+connection.domain.hostname+'/','siteUrl':connection.property_url,'languageCode':'pt-BR'},inspection=True)
    connection.data={'start':str(start),'end':str(end),'analytics':analytics,'sitemaps':sitemaps,'inspection':inspection}
    connection.save()
