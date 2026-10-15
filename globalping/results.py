"""Normalize only documented upstream fields; absent values remain None."""
import math


def number(value):
    return value if type(value) in (float,int) and math.isfinite(value) else None


def normalize(data,kind):
    rows=[]; signatures=[]
    for item in data.get('results',[]):
        if not isinstance(item,dict): continue
        probe=item.get('probe') or {}; result=item.get('result') or {}
        if not isinstance(probe,dict) or not isinstance(result,dict): continue
        latitude=number(probe.get('latitude')); longitude=number(probe.get('longitude'))
        if latitude is None or longitude is None or not (-90<=latitude<=90 and -180<=longitude<=180): latitude=longitude=None
        row={'city':probe.get('city'),'country':probe.get('country'),'network':probe.get('network'),'asn':probe.get('asn'),'latitude':latitude,'longitude':longitude,'status':result.get('status'),'address':result.get('resolvedAddress'),'hostname':result.get('resolvedHostname'),'raw_output':result.get('rawOutput'),'failure_source':result.get('failureSource')}
        timings=result.get('timings') or {}
        if kind=='ping':
            stats=result.get('stats') or {}
            row.update({key:number(stats.get(key)) for key in ('min','avg','max','loss')})
        elif kind=='traceroute':
            row['hops']=[]
            for index,hop in enumerate(result.get('hops') or [],1):
                rtts=[number(t.get('rtt')) for t in hop.get('timings',[]) if isinstance(t,dict)]
                row['hops'].append({'number':index,'address':hop.get('resolvedAddress'),'hostname':hop.get('resolvedHostname'),'rtts':rtts,'no_reply':not any(r is not None for r in rtts)})
        elif kind=='dns':
            row['answers']=[{key:answer.get(key) for key in ('name','type','ttl','class','value')} for answer in result.get('answers') or [] if isinstance(answer,dict)]
            row.update(resolver=result.get('resolver'),dns_status=result.get('statusCodeName'),dns_code=result.get('statusCode'),total=number(timings.get('total')) if isinstance(timings,dict) else None)
            # TTL and answer order differ naturally; compare returned RRsets + status.
            if result.get('status')=='finished':
                signature=(row['dns_code'],tuple(sorted({(str(a['name']).lower(),str(a['type']),str(a['class']),str(a['value'])) for a in row['answers']})))
                signatures.append(signature)
        elif kind=='http':
            headers=result.get('headers') or {}
            row.update(http_status=result.get('statusCode'),http_status_name=result.get('statusCodeName'),location=next((v for k,v in headers.items() if k.lower()=='location'),None),timings={key:number(timings.get(key)) for key in ('total','dns','tcp','tls','firstByte','download')} if isinstance(timings,dict) else {},tls=result.get('tls'))
        rows.append(row)
    return {'rows':rows,'completed':sum(r['status'] not in (None,'in-progress') for r in rows),'dns_comparable':len(signatures),'dns_different':len(set(signatures))>1 if len(signatures)>1 else None,'provider_status':data.get('status')}
