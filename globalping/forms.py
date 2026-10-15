from django import forms
from .validation import target

COUNTRIES = [('BR','Brasil'),('US','Estados Unidos'),('CA','Canadá'),('AR','Argentina'),('CL','Chile'),('MX','México'),('PT','Portugal'),('DE','Alemanha'),('FR','França'),('GB','Reino Unido'),('NL','Países Baixos'),('JP','Japão'),('SG','Singapura'),('IN','Índia'),('AU','Austrália'),('ZA','África do Sul')]
CONTINENTS = [('SA','América do Sul'),('NA','América do Norte'),('EU','Europa'),('AS','Ásia'),('AF','África'),('OC','Oceania')]
LOCATIONS = [('world','Mundo — seleção automática')] + [('country:'+code,label) for code,label in COUNTRIES] + [('continent:'+code,label+' (continente)') for code,label in CONTINENTS]


class MeasurementForm(forms.Form):
    authorized = forms.BooleanField(label="Autorização para testar o destino", required=True)
    target = forms.CharField(label='IP ou domínio público', max_length=2048, widget=forms.TextInput(attrs={'placeholder':'exemplo.com.br ou 1.1.1.1','autocomplete':'off','spellcheck':'false'}))
    kind = forms.ChoiceField(label='Tipo de teste', choices=[('ping','Ping Mundial'),('traceroute','Traceroute Mundial'),('dns','DNS Mundial'),('http','HTTP Mundial')])
    locations = forms.MultipleChoiceField(label='Países ou regiões', choices=LOCATIONS, initial=['country:BR','country:US','continent:EU'], widget=forms.SelectMultiple(attrs={'size':5,'aria-describedby':'locations-help'}))
    probes = forms.IntegerField(label='Total máximo de sondas', min_value=1, max_value=50, initial=3)
    record_type = forms.ChoiceField(label='Registro DNS', choices=[(x,x) for x in ['A','AAAA','MX','NS','TXT','CNAME']], initial='A', required=False)

    def __init__(self,*args,policy,**kwargs):
        super().__init__(*args,**kwargs)
        self.policy=policy
        self.fields['probes'].max_value=policy.max_probes
        self.fields['probes'].widget.attrs['max']=policy.max_probes
        self.fields['probes'].initial=min(3,policy.max_probes)

    def clean(self):
        data=super().clean()
        if 'target' not in data or 'kind' not in data: return data
        try: host,protocol,path=target(data['target'],data['kind'])
        except ValueError as exc: self.add_error('target',str(exc)); return data
        if data.get('probes',1)>self.policy.max_probes: self.add_error('probes','Quantidade acima do limite atual.')
        places=data.get('locations',[])
        if 'world' in places and len(places)>1: self.add_error('locations','Escolha Mundo sozinho ou selecione países e continentes.')
        if len(places)>data.get('probes',0): self.add_error('locations','Use ao menos uma sonda por localidade selecionada.')
        if len(places)>10: self.add_error('locations','Selecione no máximo 10 localidades.')
        payload={'type':data['kind'],'target':host,'limit':data.get('probes',1),'inProgressUpdates':True,'timeout':30}
        payload['locations']=[dict([place.split(':',1)]) for place in places if place!='world'] or [{}]
        if data['kind']=='dns': payload['measurementOptions']={'query':{'type':data.get('record_type') or 'A'}}
        elif data['kind']=='http': payload['measurementOptions']={'protocol':protocol,'request':{'method':'HEAD','path':path}}
        elif data['kind']=='ping': payload['measurementOptions']={'packets':3}
        data['target']=host
        data['payload']=payload
        return data
