"""Public HTTP client: resolve once per hop, connect to validated IP, retain TLS SNI."""
import http.client
import ipaddress
import socket
import ssl
import time
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit, urljoin, quote
from django.conf import settings

class UnsafeURL(ValueError): pass

def normalize_url(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 33 or ord(c)==127 for c in value) or '\\' in value:
        raise UnsafeURL('URL inválida; use HTTP ou HTTPS sem espaços ou credenciais.')
    try:
        p = urlsplit(value)
        if p.scheme.lower() not in ('http','https') or not p.hostname or p.username is not None or p.password is not None:
            raise ValueError()
        host = p.hostname.encode('idna').decode().lower().rstrip('.')
        if '%' in host or p.port not in (None,80,443): raise ValueError()
        # Reject literal non-public IPs immediately; DNS is checked again at connection.
        try: ip = ipaddress.ip_address(host)
        except ValueError: ip = None
        if ip is not None and (not ip.is_global or ip.is_reserved or ip.is_multicast or getattr(ip,'ipv4_mapped',None)):
            raise UnsafeURL('Endereço de rede não permitido.')
        netloc = f'[{host}]' if ':' in host else host
        if p.port: netloc += ':'+str(p.port)
        return urlunsplit((p.scheme.lower(),netloc,quote(p.path or '/',safe="/%:@!$&'()*+,;=-._~"),quote(p.query,safe="=&%/:?@!$'()*+,;~-._"),''))
    except (ValueError,UnicodeError) as exc:
        raise UnsafeURL('URL inválida ou destino não permitido.') from exc

def public_addresses(host,port):
    try: addresses = socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
    except socket.gaierror as exc: raise UnsafeURL('Não foi possível resolver o domínio.') from exc
    if not addresses: raise UnsafeURL('Domínio sem endereço público.')
    for _,_,_,_,addr in addresses:
        ip = ipaddress.ip_address(addr[0])
        if not ip.is_global or ip.is_reserved or ip.is_multicast or getattr(ip,'ipv4_mapped',None):
            raise UnsafeURL('Destino privado, reservado ou interno bloqueado.')
    return addresses

@dataclass
class Response:
    url: str
    status: int
    headers: dict
    body: bytes
    redirects: list
    elapsed: float
    certificate_expires: str = ''
    @property
    def text(self): return self.body.decode('utf-8',errors='replace')

class PinnedHTTP(http.client.HTTPConnection):
    def __init__(self,host,port,address,timeout):
        super().__init__(host,port,timeout=timeout)
        self.address = address
    def connect(self):
        family,kind,proto,_,addr = self.address
        self.sock = socket.socket(family,kind,proto)
        self.sock.settimeout(self.timeout)
        self.sock.connect(addr)
        if self.sock.getpeername()[0] != addr[0]:
            self.sock.close()
            raise UnsafeURL('Destino conectado não corresponde ao IP validado.')

class PinnedHTTPS(PinnedHTTP):
    def connect(self):
        super().connect()
        self.sock = ssl.create_default_context().wrap_socket(self.sock,server_hostname=self.host)

def fetch(url, *, max_redirects=3, method='GET', same_host=None):
    from core.models import BlockedHost
    url = normalize_url(url)
    hops=[]; start=time.monotonic()
    deadline = start + settings.HTTP_TIMEOUT * 2
    for step in range(max_redirects+1):
        p=urlsplit(url); host=p.hostname
        if same_host and host!=same_host: raise UnsafeURL('Redirecionamento para outro domínio bloqueado.')
        if BlockedHost.objects.filter(hostname=host).exists(): raise UnsafeURL('Domínio bloqueado por abuso.')
        port=p.port or (443 if p.scheme=='https' else 80)
        addresses=public_addresses(host,port)
        remaining=deadline-time.monotonic()
        if remaining<=0: raise UnsafeURL('Tempo total de consulta excedido.')
        conn=(PinnedHTTPS if p.scheme=='https' else PinnedHTTP)(host,port,addresses[0],min(settings.HTTP_TIMEOUT,remaining))
        try:
            conn.request(method,urlunsplit(('','',p.path or '/',p.query,'')),headers={'User-Agent':'LignetSEO/1.0 (+https://lignetbrasil.com.br/ferramentas/seo/)','Accept-Encoding':'identity','Connection':'close'})
            cert = conn.sock.getpeercert().get('notAfter','') if p.scheme=='https' else ''
            res=conn.getresponse()
            headers={k.lower():v for k,v in res.getheaders()}
            if res.status in (301,302,303,307,308) and 'location' in headers:
                if step==max_redirects: raise UnsafeURL('Limite de redirecionamentos excedido.')
                hops.append({'url':url,'status':res.status})
                url=normalize_url(urljoin(url,headers['location']))
                continue
            if headers.get('content-encoding','identity').lower() not in ('identity',''):
                raise UnsafeURL('Resposta comprimida não aceita.')
            if int(headers.get('content-length','0'))>settings.MAX_RESPONSE_BYTES:
                raise UnsafeURL('Resposta maior que o limite permitido.')
            chunks=[]; size=0
            while True:
                if time.monotonic()>deadline: raise UnsafeURL('Tempo total de consulta excedido.')
                chunk=res.read(min(65536,settings.MAX_RESPONSE_BYTES+1-size))
                if not chunk: break
                chunks.append(chunk); size+=len(chunk)
                if size>settings.MAX_RESPONSE_BYTES: raise UnsafeURL('Resposta maior que o limite permitido.')
            return Response(url,res.status,headers,b''.join(chunks),hops,round(time.monotonic()-start,3),cert)
        finally: conn.close()
    raise UnsafeURL('Redirecionamento inválido.')
