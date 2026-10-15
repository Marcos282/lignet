import ipaddress
import re
import socket
from urllib.parse import urlsplit
from core.network import normalize_url, public_addresses

FORBIDDEN_SUFFIXES = ('localhost','local','internal','lan','home','test','invalid','onion','arpa')


def target(value, kind):
    value = value.strip()
    if not value or len(value)>2048 or any(ord(c)<33 or ord(c)==127 for c in value):
        raise ValueError('Informe um IP ou domínio público válido.')
    protocol = 'HTTPS'
    path = '/'
    if '://' in value:
        if kind != 'http': raise ValueError('Neste teste, informe somente IP ou domínio, sem protocolo ou caminho.')
        p = urlsplit(normalize_url(value))
        if p.query or p.fragment: raise ValueError('Não envie parâmetros ou tokens. Use uma URL sem query string.')
        if p.port: raise ValueError('Portas personalizadas não são permitidas.')
        value = p.hostname
        protocol = p.scheme.upper()
        path = p.path
    # Bare IPv6 is accepted; URL brackets are handled above.
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        ip = None
    if ip:
        if not ip.is_global or ip.is_reserved or ip.is_multicast or getattr(ip, 'ipv4_mapped', None) or getattr(ip, 'sixtofour', None) or getattr(ip, 'teredo', None):
            raise ValueError('IPs privados, locais, reservados ou de metadados não são permitidos.')
        return str(ip), protocol, path
    try: value = value.rstrip('.').encode('idna').decode().lower()
    except UnicodeError: raise ValueError('Domínio inválido.')
    if len(value)>253 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})', value):
        raise ValueError('Informe um domínio público completo, sem portas ou credenciais.')
    if any(value == suffix or value.endswith('.'+suffix) for suffix in FORBIDDEN_SUFFIXES):
        raise ValueError('Domínios locais e reservados não são permitidos.')
    return value, protocol, path


def validate_dns(host, kind):
    """Executed in the worker; no target connection is made by Django."""
    from core.models import BlockedHost
    if BlockedHost.objects.filter(hostname=host).exists(): raise ValueError('Destino bloqueado pelo administrador.')
    try:
        ipaddress.ip_address(host)
        target(host, kind)
        return
    except ValueError:
        # Validation below still rejects a malformed/non-public literal.
        target(host, kind)
    try: public_addresses(host,443)
    except ValueError as exc:
        # A DNS-only name may legitimately have MX/TXT but no A/AAAA.
        # Only EAI_NONAME/NODATA is accepted; private/mixed DNS stays blocked.
        cause = exc.__cause__
        if kind == 'dns' and isinstance(cause, socket.gaierror) and cause.errno in (socket.EAI_NONAME, getattr(socket,'EAI_NODATA',socket.EAI_NONAME)):
            return
        raise ValueError('O domínio não resolve exclusivamente para IPs públicos.') from exc
