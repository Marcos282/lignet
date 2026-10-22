export const SPLITTERS = {2:3.7,4:7.2,8:10.5,16:13.7,32:17,64:20.5,128:24};
export const TYPES = {olt:'OLT GPON',pon:'Porta PON',splitter:'Splitter',cto:'CTO',onu:'ONU',splice:'Caixa de emenda',fiber:'Trecho de fibra'};
export const PROFILES = [
 {id:'custom',label:'Personalizado',manufacturer:'',model:'',opticalClass:''},
 {id:'huawei-ma5800',label:'Huawei MA5800 — informar módulo',manufacturer:'Huawei',model:'MA5800',opticalClass:''},
 {id:'huawei-ma5608t',label:'Huawei MA5608T — informar módulo',manufacturer:'Huawei',model:'MA5608T',opticalClass:''},
 {id:'zte-c320',label:'ZTE C320 — informar módulo',manufacturer:'ZTE',model:'C320',opticalClass:''},
 {id:'zte-c600',label:'ZTE C600 — informar módulo',manufacturer:'ZTE',model:'C600',opticalClass:''},
 {id:'generic-b',label:'Genérico GPON B+ — configurar óptica',manufacturer:'Genérico',model:'GPON',opticalClass:'B+'},
 {id:'generic-c',label:'Genérico GPON C+ — configurar óptica',manufacturer:'Genérico',model:'GPON',opticalClass:'C+'}
];
export const optical = () => ({tx:null,sensitivity:null,overload:null});
export const fiber = () => ({km:0,attenuationDown:0.25,attenuationUp:0.35,connectors:0,connectorLoss:0.3,splices:0,spliceLoss:0.1,extra:0});
export const emptyProject = () => ({version:1,name:'Meu projeto FTTH',settings:{margin:3,wavelengthDown:1490,wavelengthUp:1310},nodes:[],edges:[]});
export function createNode(type,x=100,y=100,ratio=8) {
 if (!Object.hasOwn(TYPES,type)) throw Error('Componente desconhecido.');
 return {id:crypto.randomUUID(),type,label:type==='splitter'?`Splitter 1:${ratio}`:TYPES[type],x,y,outputs:type==='olt'?16:type==='onu'?0:type==='splitter'?ratio:1,ratio:type==='splitter'?ratio:null,lossDown:type==='splitter'?SPLITTERS[ratio]:0,lossUp:type==='splitter'?SPLITTERS[ratio]:0,manufacturer:'',model:'',opticalClass:'',down:optical(),up:optical(),fiber:fiber()};
}
function number(v,min,max,name,optional=false,integer=false) {
 if(optional && v===null) return;
 if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max||(integer&&!Number.isInteger(v))) throw Error(`Valor inválido: ${name}.`);
}
function string(v,max,name) {if(typeof v!=='string'||v.length>max) throw Error(`Texto inválido: ${name}.`);}
function validateFiber(f) {
 if(!f||typeof f!=='object') throw Error('Parâmetros de fibra ausentes.');
 for(const key of ['km','attenuationDown','attenuationUp','connectorLoss','spliceLoss','extra']) number(f[key],0,10000,key);
 for(const key of ['connectors','splices']) number(f[key],0,10000,key,false,true);
}
export function capacity(n) {return n.type==='onu'?0:n.outputs;}
export function connectionError(project,from,to,port) {
 const a=project.nodes.find(n=>n.id===from),b=project.nodes.find(n=>n.id===to);
 if(!a||!b) return 'Selecione dois componentes existentes.';
 if(from===to) return 'Um componente não pode conectar a si mesmo.';
 if(b.type==='olt'||a.type==='onu'||(b.type==='pon'&&a.type!=='olt')) return 'Conexão incompatível entre estes equipamentos.';
 if(!Number.isInteger(port)||port<0||port>=capacity(a)) return 'Saída fora da capacidade do componente.';
 if(project.edges.some(e=>e.from===from&&e.port===port)) return 'Esta saída já está ocupada.';
 if(project.edges.some(e=>e.to===to)) return 'O componente já possui uma entrada.';
 const seen=new Set(); let cursor=from;
 while(cursor){if(cursor===to) return 'Conexões circulares não são permitidas.';if(seen.has(cursor))return 'Ciclo detectado.';seen.add(cursor);cursor=project.edges.find(e=>e.to===cursor)?.from;}
 return '';
}
export function validateProject(raw) {
 if(!raw||typeof raw!=='object'||raw.version!==1) throw Error('Versão de projeto inválida.');
 string(raw.name,120,'nome');
 if(!Array.isArray(raw.nodes)||raw.nodes.length>500||!Array.isArray(raw.edges)||raw.edges.length>500) throw Error('Limite de 500 componentes e conexões.');
 const s=raw.settings;
 if(!s) throw Error('Configurações ausentes.');
 number(s.margin,0,100,'margem'); number(s.wavelengthDown,800,1700,'comprimento de onda downstream');number(s.wavelengthUp,800,1700,'comprimento de onda upstream');
 const ids=new Set();
 for(const n of raw.nodes){
  string(n.id,80,'identificador'); if(!n.id||ids.has(n.id)||!Object.hasOwn(TYPES,n.type)) throw Error('Identificador duplicado ou componente inválido.'); ids.add(n.id);
  string(n.label,100,'rótulo');for(const key of ['manufacturer','model','opticalClass'])string(n[key],100,key);
  number(n.x,-100000,100000,'posição X');number(n.y,-100000,100000,'posição Y');
  number(n.outputs,0,128,'saídas',false,true);
  if(n.type==='splitter'&&(!Object.hasOwn(SPLITTERS,n.ratio)||n.outputs!==n.ratio)) throw Error('Capacidade do splitter inválida.');
  if(n.type==='onu'&&n.outputs!==0||!['olt','splitter','onu'].includes(n.type)&&n.outputs!==1||n.type==='olt'&&n.outputs<1) throw Error('Quantidade de portas inválida.');
  number(n.lossDown,0,100,'perda downstream');number(n.lossUp,0,100,'perda upstream');
  for(const direction of ['down','up']){
   if(!n[direction])throw Error('Parâmetros ópticos ausentes.');
   for(const key of ['tx','sensitivity','overload']) number(n[direction][key],-100,50,key,true);
   if(n[direction].sensitivity!==null&&n[direction].overload!==null&&n[direction].sensitivity>=n[direction].overload)throw Error('A sensibilidade deve ser menor que a sobrecarga.');
  }
  validateFiber(n.fiber);
 }
 const partial={nodes:raw.nodes,edges:[]}, edgeIds=new Set();
 for(const e of raw.edges){string(e.id,80,'conexão'); if(!e.id||edgeIds.has(e.id)||ids.has(e.id))throw Error('Conexão duplicada.');edgeIds.add(e.id);validateFiber(e.fiber);const error=connectionError(partial,e.from,e.to,e.port);if(error)throw Error(error);partial.edges.push(e);}
 // Rebuild an allowlisted object; imported properties never become executable DOM or code.
 return {version:1,name:raw.name,settings:{margin:s.margin,wavelengthDown:s.wavelengthDown,wavelengthUp:s.wavelengthUp},nodes:raw.nodes.map(n=>({id:n.id,type:n.type,label:n.label,x:n.x,y:n.y,outputs:n.outputs,ratio:n.type==='splitter'?n.ratio:null,lossDown:n.lossDown,lossUp:n.lossUp,manufacturer:n.manufacturer,model:n.model,opticalClass:n.opticalClass,down:{tx:n.down.tx,sensitivity:n.down.sensitivity,overload:n.down.overload},up:{tx:n.up.tx,sensitivity:n.up.sensitivity,overload:n.up.overload},fiber:{...fiber(),...Object.fromEntries(Object.keys(fiber()).map(k=>[k,n.fiber[k]]))}})),edges:raw.edges.map(e=>({id:e.id,from:e.from,to:e.to,port:e.port,fiber:Object.fromEntries(Object.keys(fiber()).map(k=>[k,e.fiber[k]]))}))};
}
export function fiberLoss(f,direction){return f.km*f[direction==='down'?'attenuationDown':'attenuationUp']+f.connectors*f.connectorLoss+f.splices*f.spliceLoss+f.extra;}
export function diagnose(rx,receiver,margin){
 if(rx===null||receiver.sensitivity===null||receiver.overload===null)return {status:'unknown',label:'Dados insuficientes',margin:null};
 const available=Math.min(rx-receiver.sensitivity,receiver.overload-rx);
 return {status:available<0?'bad':available<margin?'warning':'good',label:available<0?'Fora dos limites':available<margin?'Margem insuficiente':'Dentro dos limites',margin:available};
}
export function calculate(project,direction='down'){
 const nodes=new Map(project.nodes.map(n=>[n.id,n])),incoming=new Map(project.edges.map(e=>[e.to,e]));
 return project.nodes.filter(n=>n.type==='onu').map(onu=>{
  const path=[],edges=[],seen=new Set();let current=onu;
  while(current){if(seen.has(current.id))return {id:onu.id,status:'unknown',label:'Ciclo inválido',rx:null,margin:null};seen.add(current.id);path.unshift(current);const edge=incoming.get(current.id);if(!edge)break;edges.unshift(edge);current=nodes.get(edge.from);}
  const root=path[0],valid=root?.type==='olt';
  // A PON module is the optical endpoint; its OLT link is logical.
  const ponIndex=path.findIndex(n=>n.type==='pon');
  const opticalPath=ponIndex>=0?path.slice(ponIndex):path;
  const opticalEdges=ponIndex>=0?edges.slice(ponIndex):edges;
  const loss=opticalPath.reduce((sum,n)=>sum+(['olt','pon','onu'].includes(n.type)?0:n[direction==='down'?'lossDown':'lossUp'])+(n.type==='fiber'?fiberLoss(n.fiber,direction):0),0)+opticalEdges.reduce((sum,e)=>sum+fiberLoss(e.fiber,direction),0);
  const distance=opticalPath.filter(n=>n.type==='fiber').reduce((sum,n)=>sum+n.fiber.km,0)+opticalEdges.reduce((sum,e)=>sum+e.fiber.km,0);
  const source=direction==='down'?(path.find(n=>n.type==='pon'&&n.down.tx!==null)||root):onu;
  const receiver=direction==='down'?onu:(path.find(n=>n.type==='pon')||root);
  const tx=source?.[direction].tx??null;
  const rx=valid&&tx!==null?tx-loss:null;
  return {id:onu.id,loss,distance,tx,rx,root:valid?root.id:null,path:path.map(n=>n.id),...diagnose(rx,receiver?.[direction]||optical(),project.settings.margin),...(!valid?{status:'unknown',label:'Sem caminho até uma OLT'}:{})};
 });
}

export function downstreamLevels(project){
 const levels=new Map(),nodes=new Map(project.nodes.map(n=>[n.id,n])),incoming=new Map(project.edges.map(e=>[e.to,e]));
 function visit(n,seen=new Set()){
  if(levels.has(n.id))return levels.get(n.id);
  if(seen.has(n.id))return null;
  seen.add(n.id);
  let rx=null;
  if(n.type==='olt')rx=n.down.tx;
  else {const edge=incoming.get(n.id),parent=edge?nodes.get(edge.from):null;if(parent){const power=visit(parent,seen);if(power!==null)rx=power-fiberLoss(edge.fiber,'down')-(n.type==='onu'?0:n.lossDown)-(n.type==='fiber'?fiberLoss(n.fiber,'down'):0);if(n.type==='pon')rx=power;if(n.type==='pon'&&n.down.tx!==null){let root=parent;const traced=new Set();while(root&&root.type!=='olt'&&!traced.has(root.id)){traced.add(root.id);root=nodes.get(incoming.get(root.id)?.from);}if(root?.type==='olt')rx=n.down.tx;}}}
  levels.set(n.id,rx);return rx;
 }
 for(const n of project.nodes)visit(n);
 return levels;
}
