from django import forms
from core.network import normalize_url
class AuditForm(forms.Form):
    url=forms.CharField(label='Endereço do site',max_length=2048,widget=forms.URLInput(attrs={'placeholder':'https://seusite.com.br','class':'form-control form-control-lg','autocomplete':'url'}))
    def clean_url(self):
        try: return normalize_url(self.cleaned_data['url'])
        except ValueError as exc: raise forms.ValidationError(str(exc))
class SitemapForm(forms.Form):
    urls=forms.CharField(label='Uma URL por linha',max_length=5000000,widget=forms.Textarea(attrs={'rows':9,'placeholder':'https://seusite.com.br/\nhttps://seusite.com.br/contato/'}))
class RobotsForm(forms.Form):
    agent=forms.CharField(label='User-agents (um por linha; mesmas regras para todos)',initial='*',max_length=2000,widget=forms.Textarea(attrs={'rows':2}))
    public=forms.CharField(label='Diretórios públicos (um por linha)',required=False,initial='/',max_length=20000,widget=forms.Textarea(attrs={'rows':3}))
    blocked=forms.CharField(label='Diretórios bloqueados (um por linha)',required=False,max_length=20000,widget=forms.Textarea(attrs={'rows':3,'placeholder':'/admin/'}))
    sitemap=forms.CharField(label='URL do sitemap',required=False,max_length=2048)
class DomainForm(forms.Form):
    hostname=forms.CharField(label='Domínio',max_length=253,widget=forms.TextInput(attrs={'placeholder':'seusite.com.br'}))
    def clean_hostname(self):
        import re
        value=self.cleaned_data['hostname'].strip().lower().rstrip('.')
        try: value=value.encode('idna').decode()
        except UnicodeError: raise forms.ValidationError('Domínio inválido.')
        if not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',value): raise forms.ValidationError('Informe somente o domínio, sem protocolo ou caminho.')
        return value
