class PrivateResponseMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if request.path.startswith(('/painel/','/relatorios/','/conta/','/dominios/','/integracoes/','/admin/','/api/globalping/')) or request.method!='GET':
            response['X-Robots-Tag']='noindex, nofollow, noarchive'
            response['Cache-Control']='private, no-store'
            response['Referrer-Policy']='same-origin'
        return response

class TrustedProxyIPMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        from django.conf import settings
        import ipaddress
        if request.META.get('REMOTE_ADDR') in settings.TRUSTED_PROXY_IPS:
            try: request.META['REMOTE_ADDR']=str(ipaddress.ip_address(request.META.get('HTTP_X_REAL_IP','')))
            except ValueError: pass
        return self.get_response(request)
