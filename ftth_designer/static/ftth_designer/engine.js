// Stage 1: validated visual graph and primitives. Full directional budgets come in stage 2.
export const RATIOS = [5,10,15,20,25,30,35,40,45,50];
export const BALANCED = {2:3.7,4:7.2,8:10.5,16:13.7,32:17,64:20.5};
export const TYPES = {olt:'OLT GPON',olt_xgs:'OLT XGS-PON',asymmetric:'Splitter assimétrico',balanced:'Splitter balanceado',cto:'CTO',onu:'ONU / ONT',splice:'Caixa de emenda',fiber:'Segmento de fibra'};
export const ATTENUATION = {'1310':0.35,'1490':0.25,'1550':0.20,'1577':null,'1270':null};
const num=(v,min=0,max=100000)=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;
export function asymmetricLoss(percent,excess=0,real=null){
 if(!num(percent,0.001,99.999)||!num(excess)||real!==null&&!num(real))throw Error('Perda ou proporção inválida.');
 return real===null?-10*Math.log10(percent/100)+excess:real;
}
export const fiber=()=>({km:0,attenuation:{...ATTENUATION},connectors:0,connectorLoss:0.3,splices:0,spliceLoss:0.1,additional:0});
export function fiberLoss(f,wavelength){const alpha=f.attenuation[String(wavelength)];return alpha===null||alpha===undefined?null:f.km*alpha+f.connectors*f.connectorLoss+f.splices*f.spliceLoss+f.additional;}
export const optics=()=>({txMin:null,txMax:null,sensitivity:null,overload:null});
export const empty=()=>({version:1,name:'Novo desenho FTTH',technology:'GPON',margin:3,nodes:[],edges:[]});
export function createNode(type,x=80,y=80,ratio=type==='balanced'?8:10){
 if(!Object.hasOwn(TYPES,type))throw Error('Componente inválido.');
 return {id:crypto.randomUUID(),type,name:TYPES[type],x,y,ratio,ports:type==='onu'?0:type==='asymmetric'?2:type==='balanced'?ratio:type==='cto'?8:type.startsWith('olt')?16:1,opticalClass:'',manufacturer:'',model:'',down:optics(),up:optics(),excess:0,realDown:[null,null],realUp:[null,null],balancedDown:type==='balanced'?BALANCED[ratio]:0,balancedUp:type==='balanced'?BALANCED[ratio]:0,fiber:fiber()};
}
export function portLabel(node,port){return node.type==='asymmetric'?`${port===0?node.ratio:100-node.ratio}% · saída ${port+1}`:`Saída ${port+1}`;}
export function connectionError(p,from,to,port,targetPort=0){
 const a=p.nodes.find(n=>n.id===from),b=p.nodes.find(n=>n.id===to);
 if(!a||!b)return 'Origem ou destino inexistente.';
 if(a===b)return 'Um componente não pode conectar a si mesmo.';
 if(a.type==='onu'||b.type.startsWith('olt'))return 'Portas incompatíveis: ONU é terminal e OLT é origem.';
 if(!Number.isInteger(port)||port<0||port>=a.ports||targetPort!==0)return 'Porta fora da capacidade física.';
 if(p.edges.some(e=>e.from===from&&e.port===port))return 'Saída já ocupada.';
 if(p.edges.some(e=>e.to===to))return 'A entrada do destino já está ocupada.';
 let cursor=from;const seen=new Set();
 while(cursor){if(cursor===to||seen.has(cursor))return 'Conexão circular não permitida.';seen.add(cursor);cursor=p.edges.find(e=>e.to===cursor)?.from;}
 return '';
}
function checkFiber(f){if(!f||typeof f!=='object')throw Error('Fibra inválida.');for(const key of ['km','connectors','connectorLoss','splices','spliceLoss','additional'])if(!num(f[key]))throw Error('Distância ou perda inválida.');for(const key of ['connectors','splices'])if(!Number.isInteger(f[key]))throw Error('Quantidades devem ser inteiras.');for(const wavelength of Object.keys(ATTENUATION))if(f.attenuation?.[wavelength]!==null&&!num(f.attenuation?.[wavelength],0,100))throw Error('Atenuação inválida.');}
export function validate(raw){
 if(!raw||raw.version!==1||typeof raw.name!=='string'||raw.name.length>120||!['GPON','XGS-PON'].includes(raw.technology)||!num(raw.margin,0,100)||!Array.isArray(raw.nodes)||!Array.isArray(raw.edges)||raw.nodes.length>300||raw.edges.length>300)throw Error('Desenho inválido ou limite de 300 componentes excedido.');
 const ids=new Set();
 for(const n of raw.nodes){
  if(!n||typeof n.id!=='string'||!n.id||n.id.length>80||ids.has(n.id)||!Object.hasOwn(TYPES,n.type)||typeof n.name!=='string'||n.name.length>100||!num(n.x,-100000)||!num(n.y,-100000)||!Number.isInteger(n.ports)||!num(n.ports,0,128))throw Error('Componente inválido.');ids.add(n.id);
  if(n.type==='asymmetric'&&(!RATIOS.includes(n.ratio)||n.ports!==2)||n.type==='balanced'&&(!Object.hasOwn(BALANCED,n.ratio)||n.ports!==n.ratio)||n.type==='onu'&&n.ports!==0||['splice','fiber'].includes(n.type)&&n.ports!==1||['olt','olt_xgs','cto'].includes(n.type)&&n.ports<1)throw Error('Capacidade ou proporção inválida.');
  for(const key of ['manufacturer','model','opticalClass'])if(typeof n[key]!=='string'||n[key].length>100)throw Error('Referência de equipamento inválida.');
  for(const direction of ['down','up']){const o=n[direction];if(!o)throw Error('Configuração óptica ausente.');for(const key of ['txMin','txMax','sensitivity','overload'])if(o[key]!==null&&!num(o[key],-100,50))throw Error('Parâmetro óptico inválido.');if(o.txMin!==null&&o.txMax!==null&&o.txMin>o.txMax||o.sensitivity!==null&&o.overload!==null&&o.sensitivity>=o.overload)throw Error('Intervalo óptico invertido.');}
  if(!num(n.excess,0,100)||!num(n.balancedDown,0,100)||!num(n.balancedUp,0,100))throw Error('Perda inválida.');
  for(const key of ['realDown','realUp'])if(!Array.isArray(n[key])||n[key].length!==2||n[key].some(v=>v!==null&&!num(v,0,100)))throw Error('Perdas por saída inválidas.');checkFiber(n.fiber);
 }
 const partial={nodes:raw.nodes,edges:[]};
 for(const e of raw.edges){if(typeof e.id!=='string'||!e.id||e.id.length>80||ids.has(e.id))throw Error('Identificador de conexão inválido.');ids.add(e.id);const error=connectionError(partial,e.from,e.to,e.port,e.targetPort);if(error)throw Error(error);checkFiber(e.fiber);partial.edges.push(e);}
 return structuredClone(raw);
}
