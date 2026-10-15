/* All diagnostic values come from the Django API, which stores Globalping results. */
(() => {
  'use strict';
  const form = document.querySelector('#gp-form');
  if (!form) return;
  const $ = (id) => document.getElementById(id);
  const button = $('gp-submit');
  const errorBox = $('gp-error');
  const nil = (value) => value === null || value === undefined || value === '';
  const show = (value, suffix = '') => nil(value) ? '—' : `${value}${suffix}`;
  const date = (value) => value ? new Date(value).toLocaleString('pt-BR') : '—';
  const states = {queued:'Na fila',validating:'Validando destino',creating:'Iniciando medição','in-progress':'Em andamento',finished:'Concluído',failed:'Falhou',expired:'Expirado',offline:'Sonda offline'};
  const busy = (status) => ['queued','validating','creating','in-progress'].includes(status);
  let generation = 0;
  let timer;
  let map, markers;
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (!nil(text)) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  function announceError(message) {
    errorBox.textContent = message;
    errorBox.hidden = !message;
  }
  async function api(url, options = {}) {
    const response = await fetch(url, {credentials:'same-origin',cache:'no-store',...options});
    let body;
    try { body = await response.json(); }
    catch (_) { throw new Error(response.status === 403 ? 'Sessão de segurança expirada. Recarregue a página e tente novamente.' : 'O servidor não respondeu como esperado. Tente novamente mais tarde.'); }
    if (!response.ok) {
      let message = body.error || 'Não foi possível consultar o teste.';
      if (body.fields) message += ' ' + Object.values(body.fields).flat().map(e => e.message).join(' ');
      if (body.retry_after) message += ` Aguarde pelo menos ${body.retry_after} s.`;
      throw new Error(message);
    }
    return body;
  }
  function table(headers, rows) {
    const wrap = element('div', null, 'table-wrap');
    const tab = element('table', null, 'gp-table');
    const head = element('thead');
    const hrow = element('tr');
    headers.forEach(h => { const th = element('th',h); th.scope = 'col'; hrow.append(th); });
    head.append(hrow); tab.append(head);
    const body = element('tbody');
    rows.forEach(values => {
      const tr = element('tr');
      values.forEach(value => {
        const td = element('td');
        if (value instanceof Node) td.append(value); else td.textContent = show(value);
        tr.append(td);
      });
      body.append(tr);
    });
    tab.append(body); wrap.append(tab); return wrap;
  }
  function location(row) {
    return [row.city,row.country].filter(v => !nil(v)).join(', ') || 'Localidade não informada';
  }
  function locationCell(row) {
    const cell = element('div'); cell.append(element('strong',location(row)),element('small',[row.network,nil(row.asn) ? null : `AS${row.asn}`].filter(Boolean).join(' · ')));
    return cell;
  }
  function statusBadge(value) { return element('span',states[value] || show(value),'gp-row-status'); }
  function mapResults(rows) {
    if (!map) return;
    markers.clearLayers(); const bounds = [];
    rows.forEach((row,index) => {
      if (!Number.isFinite(row.latitude) || !Number.isFinite(row.longitude)) return;
      const point = [row.latitude,row.longitude]; bounds.push(point);
      const pin = element('span',index+1);
      const icon = L.divIcon({html:pin,className:`gp-pin ${row.status === 'failed' ? 'gp-pin-failed' : row.status === 'in-progress' ? 'gp-pin-running' : ''}`,iconSize:[28,28],iconAnchor:[14,14]});
      const popup = element('div'); popup.append(element('strong',location(row)),element('p',`${states[row.status] || show(row.status)} · ${show(row.address)}`));
      L.marker(point,{icon,title:location(row)}).bindPopup(popup).addTo(markers);
    });
    if (bounds.length) map.fitBounds(bounds,{padding:[35,35],maxZoom:5,animate:false});
    $('map-note').textContent = rows.length ? `${bounds.length} de ${rows.length} sondas com coordenadas retornadas pela API. Os pontos representam as origens das medições.` : 'Aguardando localidades retornadas pela Globalping.';
  }
  function rawDetails(row,parent) {
    if (nil(row.raw_output)) return;
    const details = element('details'); details.append(element('summary','Saída técnica retornada pela sonda'),element('pre',row.raw_output)); parent.append(details);
  }
  function renderDetails(data, rows) {
    const container = element('div',null,data.type === 'traceroute' ? 'gp-route-comparison' : '');
    rows.forEach(row => {
      const card = element('article',null,'gp-result-detail');
      card.append(element('h3',location(row)));
      if (data.type === 'traceroute') {
        card.append(table(['Salto','IP','Hostname','RTT retornado (ms)','Resposta'],(row.hops || []).map(hop => [hop.number,hop.address,hop.hostname,(hop.rtts || []).map(v => show(v)).join(' / '),hop.no_reply ? 'Sem resposta' : 'Resposta recebida'])));
        if (!(row.hops || []).length) card.append(element('p','Nenhum salto disponível nesta resposta.','gp-small'));
      } else if (data.type === 'dns') {
        card.append(element('p',`Resolver: ${show(row.resolver)} · Resposta: ${show(row.dns_status)} · ${show(row.total,' ms')}`,'gp-small'));
        card.append(table(['Nome','Tipo','Valor','TTL (s)'],(row.answers || []).map(a => [a.name,a.type,a.value,a.ttl])));
        if (!(row.answers || []).length) card.append(element('p','Nenhum registro retornado nesta resposta.','gp-small'));
      } else if (data.type === 'http') {
        const t = row.timings || {};
        card.append(table(['DNS','TCP','TLS','Primeiro byte','Download','Total'],[[show(t.dns,' ms'),show(t.tcp,' ms'),show(t.tls,' ms'),show(t.firstByte,' ms'),show(t.download,' ms'),show(t.total,' ms')]]));
        card.append(element('p',`Location retornado: ${show(Array.isArray(row.location) ? row.location.join(', ') : row.location)}`,'gp-small'));
        if (row.tls) { const tls = element('details'); tls.append(element('summary','Certificado TLS retornado'),element('pre',JSON.stringify(row.tls,null,2))); card.append(tls); }
      }
      if (row.failure_source) card.append(element('p',`Origem provável da falha informada pela API: ${row.failure_source}`,'gp-small'));
      rawDetails(row,card); container.append(card);
    });
    return container;
  }
  function render(data) {
    const rows = data.results?.rows || [];
    $('results-title').textContent = `${data.type.toUpperCase()} · ${data.target}`;
    $('gp-state').textContent = states[data.status] || data.status;
    $('gp-state').dataset.state = data.status;
    $('gp-progress').hidden = false;
    const count = data.probes_count;
    const done = data.results?.completed || 0;
    const bar = $('gp-progress-bar');
    if (count > 0) { bar.max = count; bar.value = Math.min(done,count); }
    else { bar.removeAttribute('value'); }
    $('gp-progress-text').textContent = count > 0 ? `${done} de ${count} sondas com resultado final.` : `${states[data.status] || data.status}. Aguardando a quantidade de sondas informada pela API.`;
    if (!busy(data.status) && !count) $('gp-progress').hidden = true;
    const meta = [`Solicitado em ${date(data.created_at)}`,data.measured_at ? `Medição de ${date(data.measured_at)}` : null,data.from_cache ? 'Resultado reutilizado do cache; não é um novo teste.' : null,data.remote_id ? `ID Globalping: ${data.remote_id}` : null];
    $('gp-meta').textContent = meta.filter(Boolean).join(' · ');
    const summary = $('gp-summary'); summary.replaceChildren();
    if (data.error) summary.append(element('p',data.error,'gp-status-message warning'));
    if (data.retry_after && busy(data.status)) summary.append(element('p',`A API pediu uma pausa de ${data.retry_after} segundos. Aguardando dentro do limite de tempo do teste.`,'gp-status-message warning'));
    if (data.type === 'dns') {
      const different = data.results?.dns_different;
      summary.append(element('p',different === true ? 'Há diferenças entre os conjuntos de registros/códigos DNS retornados. Isso pode ser normal em DNS geográfico ou cache.' : different === false ? 'Os conjuntos de registros e códigos DNS comparáveis coincidem. TTL e ordem foram desconsiderados.' : 'Ainda não há duas respostas DNS finais para comparar.',`gp-status-message${different ? ' warning' : ''}`));
    }
    if (!nil(data.usage?.remaining)) summary.append(element('p',`Cota compartilhada informada na criação: ${data.usage.remaining} testes restantes${nil(data.usage.limit) ? '' : ` de ${data.usage.limit}`}. Consumo desta criação: ${show(data.usage.consumed)}.`,'gp-small'));
    const results = $('gp-results'); results.replaceChildren();
    if (rows.length) {
      let headers = ['Localidade / rede','IP de destino'];
      if (data.type === 'ping') headers.push('Mín. (ms)','Média (ms)','Máx. (ms)','Perda (%)');
      if (data.type === 'traceroute') headers.push('Saltos retornados');
      if (data.type === 'dns') headers.push('Código DNS','Tempo (ms)','Resolver');
      if (data.type === 'http') headers.push('HTTP','Total (ms)','TCP (ms)','TLS (ms)');
      headers.push('Status da sonda');
      results.append(table(headers,rows.map(row => {
        const cells = [locationCell(row),row.address];
        if (data.type === 'ping') cells.push(row.min,row.avg,row.max,row.loss);
        if (data.type === 'traceroute') cells.push(row.hops ? row.hops.length : null);
        if (data.type === 'dns') cells.push(row.dns_status,row.total,row.resolver);
        if (data.type === 'http') cells.push(row.http_status,row.timings?.total,row.timings?.tcp,row.timings?.tls);
        cells.push(statusBadge(row.status)); return cells;
      })));
      results.append(renderDetails(data,rows));
    } else results.append(element('p',busy(data.status) ? 'As medições aparecerão assim que as sondas responderem.' : 'Nenhum resultado foi retornado.','gp-small'));
    mapResults(rows);
    button.disabled = busy(data.status);
  }
  async function watch(id, serial, started = Date.now()) {
    try {
      const url = form.dataset.statusTemplate.replace('00000000-0000-0000-0000-000000000000',encodeURIComponent(id));
      const data = await api(url);
      if (serial !== generation) return;
      render(data);
      if (busy(data.status) && Date.now()-started < 210000) timer = setTimeout(() => watch(id,serial,started),Math.max(2,data.poll_after || 2)*1000);
      else {
        if (busy(data.status)) announceError('A consulta de progresso foi pausada. Atualize o histórico para consultar este teste; nenhuma nova medição foi criada.');
        button.disabled = false;
        loadHistory();
      }
    } catch (error) { if (serial === generation) { announceError(error.message); button.disabled = false; } }
  }
  async function loadHistory() {
    const history = $('gp-history');
    try {
      const data = await api(form.dataset.history);
      history.replaceChildren();
      if (!data.measurements.length) { history.append(element('p','Você ainda não iniciou testes nesta sessão.','gp-small')); return; }
      history.append(table(['Data','Tipo / destino','Status','Resultado'],data.measurements.map(item => {
        const action = element('button','Ver resultado','btn btn-outline-primary'); action.type = 'button';
        action.addEventListener('click',() => { clearTimeout(timer); generation++; announceError(''); watch(item.id,generation); $('gp-report').scrollIntoView({behavior:'auto',block:'start'}); });
        return [date(item.created_at),`${item.type.toUpperCase()} · ${item.target}`,states[item.status] || item.status,action];
      })));
    } catch (error) { history.textContent = error.message; }
  }
  form.querySelector('[name=kind]').addEventListener('change',event => { $('dns-options').hidden = event.target.value !== 'dns'; });
  form.addEventListener('submit',async event => {
    event.preventDefault(); if (!form.reportValidity()) return;
    clearTimeout(timer); const serial = ++generation; announceError(''); button.disabled = true;
    const fd = new FormData(form);
    const data = {target:fd.get('target'),kind:fd.get('kind'),probes:fd.get('probes'),locations:fd.getAll('locations'),record_type:fd.get('record_type'),authorized:fd.get('authorized') === 'on'};
    try {
      const result = await api(form.dataset.start,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':fd.get('csrfmiddlewaretoken')},body:JSON.stringify(data)});
      if (serial !== generation) return;
      $('gp-report').scrollIntoView({behavior:'auto',block:'start'}); watch(result.id,serial); loadHistory();
    } catch (error) { if (serial === generation) { announceError(error.message); button.disabled = false; loadHistory(); } }
  });
  $('gp-history-refresh').addEventListener('click',loadHistory);
  try {
    const config = JSON.parse($('gp-map-config').textContent);
    if (!window.L) throw new Error('Mapa indisponível. Os resultados continuam disponíveis nas tabelas.');
    map = L.map('gp-map',{scrollWheelZoom:false}).setView([18,0],2);
    L.tileLayer(config.tileUrl,{attribution:config.attribution,maxZoom:18}).on('tileerror',() => { $('map-note').textContent = 'Não foi possível carregar parte do mapa. Consulte as localidades nas tabelas.'; }).addTo(map);
    markers = L.layerGroup().addTo(map);
  } catch (error) { $('map-note').textContent = error.message; }
  loadHistory();
  window.addEventListener('pagehide',() => { clearTimeout(timer); generation++; });
})();
