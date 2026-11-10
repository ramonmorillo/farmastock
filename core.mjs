export const KEYS={ledger:'farmastock.comunicadas.v1',demo:'farmastock.demo.v1'};
export const clean=s=>String(s??'').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').trim();
export const label=s=>clean(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[\s_-]+/g,'');
export function cn(value){const s=clean(value);if(!/^\d{6}$/.test(s))throw new Error(`CN «${s.slice(0,30)}»: se requieren seis dígitos, sin perder ceros ni añadir dígitos de control.`);return s;}
export function date(value,optional=false){
  let s=clean(value);if(!s&&optional)return '';
  if(/^\d{2}\/\d{2}\/\d{4}$/.test(s))s=s.slice(6)+'-'+s.slice(3,5)+'-'+s.slice(0,2);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(s)||Number.isNaN(Date.parse(s))||new Date(s).toISOString().slice(0,10)!==s)throw new Error('Fecha no válida: usa AAAA-MM-DD o DD/MM/AAAA, no números de serie de Excel.');
  return s;
}
export function parseCSV(input){
  if(input.length>5000000)throw new Error('CSV demasiado grande (máximo 5 MB).');
  const text=input.replace(/^\uFEFF/,'');
  // El separador se decide fuera de las comillas de la primera fila.
  let quoted=false,comma=0,semi=0;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"')i++;else quoted=!quoted;}else if(!quoted){if(c==='\n'||c==='\r')break;if(c===',')comma++;if(c===';')semi++;}}
  const separator=semi>comma?';':',';let rows=[],row=[],cell='',inside=false,afterQuote=false;
  function endCell(){row.push(cell);cell='';afterQuote=false;if(row.length>50)throw new Error('Máximo 50 columnas.');}
  function endRow(){endCell();if(row.some(c=>c.trim()))rows.push(row);row=[];if(rows.length>10001)throw new Error('Máximo 10 000 filas de datos.');}
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(inside){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{inside=false;afterQuote=true;}}else cell+=c;}
    else if(c===separator)endCell();
    else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;endRow();}
    else if(c==='"'){if(cell||afterQuote)throw new Error('Comillas CSV mal formadas.');inside=true;}
    else {if(afterQuote&&!/\s/.test(c))throw new Error('Texto inesperado después de una celda entrecomillada.');if(!afterQuote)cell+=c;}
    if(cell.length>12000)throw new Error('Celda demasiado extensa (máximo 12 000 caracteres).');
  }
  if(inside)throw new Error('Comillas CSV sin cerrar.');
  if(cell||row.length||afterQuote)endRow();return table(rows);
}
export function table(rows){
  const data=rows.filter(r=>r.some(v=>clean(v)));
  if(data.length<2)throw new Error('Se necesitan cabecera y al menos una fila de datos.');
  if(data.length>10001||data[0].length>50)throw new Error('Límite de 10 000 filas y 50 columnas.');
  const headers=data[0].map(clean);
  if(headers.some(h=>!h)||new Set(headers.map(label)).size!==headers.length)throw new Error('Las cabeceras deben ser distintas y no estar vacías.');
  const body=data.slice(1).map((r,i)=>{if(r.length>headers.length&&r.slice(headers.length).some(v=>clean(v)))throw new Error(`Fila ${i+2}: más columnas que la cabecera.`);return headers.map((_,j)=>clean(r[j]));});
  return {headers,rows:body};
}
export const ALIASES={cn:['cn','codigonacional'],name:['nombre','medicamento','presentacion'],id:['id','idincidencia'],start:['inicio','fechainicio'],end:['fin','fechafin','finprevisto'],description:['descripcion','observaciones','incidencia'],status:['estado','activo']};
export function suggest(headers,key){return headers.findIndex(h=>ALIASES[key].includes(label(h)));}
function get(row,mapping,key,required=false){const index=mapping[key];const value=Number.isInteger(index)&&index>=0?row[index]||'':'';if(required&&!value)throw new Error(`Falta ${key}.`);return value;}
function mappingOK(t,map,required){for(const k of required)if(!Number.isInteger(map[k])||map[k]<0||map[k]>=t.headers.length)throw new Error(`Asocia la columna ${k}.`);}
export function catalog(t,map){
  mappingOK(t,map,['cn','name']);const byCN=new Map();let duplicates=0;
  t.rows.forEach((row,i)=>{try{const code=cn(get(row,map,'cn',true)),name=get(row,map,'name',true);if(name.length>500)throw new Error('Nombre de catálogo demasiado extenso (máximo 500 caracteres).');if(!byCN.has(code))byCN.set(code,{cn:code,names:[]});const item=byCN.get(code);if(item.names.includes(name))duplicates++;else{if(item.names.length>=20)throw new Error('Más de 20 denominaciones para un CN: revisa el catálogo.');item.names.push(name);}}catch(e){throw new Error(`Catálogo, fila ${i+2}: ${e.message}`);}});
  return {items:[...byCN.values()],duplicates};
}
export function status(value){const s=label(value);if(['1','si','true','activo','activa','encurso'].includes(s))return 'active';if(['0','no','false','resuelto','resuelta','finalizado','finalizada'].includes(s))return 'resolved';return 'unknown';}
export function identity(r){return JSON.stringify([r.cn,r.id?'id:'+r.id:'inicio:'+r.start]);}
export function signature(r){return JSON.stringify([r.cn,r.id,r.start,r.end,r.description,r.status,r.status==='unknown'?r.rawStatus:'']);}
export function incidents(t,map){
  mappingOK(t,map,['cn','start','description']);const records=new Map();let duplicates=0;
  t.rows.forEach((row,i)=>{try{
    const r={cn:cn(get(row,map,'cn',true)),id:get(row,map,'id'),start:date(get(row,map,'start',true)),end:date(get(row,map,'end'),true),description:get(row,map,'description',true),rawStatus:get(row,map,'status')};r.status=status(r.rawStatus);
    if(r.id.length>200||r.rawStatus.length>200)throw new Error('ID o estado demasiado extenso (máximo 200 caracteres).');
    if(r.end&&r.end<r.start)throw new Error('El fin no puede ser anterior al inicio.');
    const key=identity(r);if(records.has(key)){if(signature(records.get(key))!==signature(r))throw new Error('Identificador de incidencia repetido con contenido distinto. Aporta un ID inequívoco o consolida el fichero.');duplicates++;}else records.set(key,r);
  }catch(e){throw new Error(`Incidencias, fila ${i+2}: ${e.message}`);}});
  return {items:[...records.values()],duplicates};
}
export function validateSource(meta,today=new Date().toLocaleDateString('sv-SE')){
  if(!meta.title?.trim())throw new Error('Identifica el fichero de incidencias.');const issued=date(meta.date);if(issued>today)throw new Error('La fecha del fichero no puede estar en el futuro.');
  if(meta.demo!==true){let u;try{u=new URL(meta.url);}catch{throw new Error('Aporta una URL HTTPS de referencia oficial AEMPS/CIMA.');}if(u.protocol!=='https:'||u.username||u.password||!['aemps.es','aemps.gob.es'].some(host=>u.hostname===host||u.hostname.endsWith('.'+host)))throw new Error('La referencia debe ser una URL HTTPS oficial AEMPS/CIMA sin credenciales.');}
  if(!['complete','partial'].includes(meta.scope))throw new Error('Indica si el fichero es completo o parcial.');
  return {...meta,date:issued};
}
export function analyze(catalogRows,incidentRows,meta,ledger=[]){
  const source=validateSource(meta),codes=new Map(catalogRows.map(c=>[c.cn,c])),seen=new Map(ledger.map(e=>[e.key,e]));
  const rows=incidentRows.filter(r=>codes.has(r.cn)).map(r=>{
    const key=identity(r),previous=seen.get(key),fingerprint=signature(r);
    return {...r,key,fingerprint,catalogNames:codes.get(r.cn).names.join(' / '),change:!previous?'new':previous.fingerprint===fingerprint?'notified':'changed',notifiedAt:previous?.at||''};
  });
  const currentKeys=new Set(incidentRows.map(identity));
  const notObserved=ledger.filter(e=>codes.has(e.cn)&&!currentKeys.has(e.key));
  return {source,rows,notObserved,unmatched:incidentRows.filter(r=>!codes.has(r.cn)).length};
}
export function loadLedger(demo=false,storage=globalThis.localStorage){
  let raw;try{raw=storage.getItem(demo?KEYS.demo:KEYS.ledger);}catch{throw new Error('El navegador no permite leer el historial local. No se ha generado una comparación sin ese control.');}
  let data;try{data=JSON.parse(raw===null?'[]':raw);}catch{throw new Error('Historial de comunicaciones dañado. No se sobrescribe; revisa o borra los datos locales.');}
  if(!Array.isArray(data)||data.length>2000||data.some(e=>!e||typeof e.key!=='string'||e.key.length>500||typeof e.fingerprint!=='string'||e.fingerprint.length>30000||typeof e.cn!=='string'||!/^\d{6}$/.test(e.cn)||typeof e.at!=='string'))throw new Error('Historial de comunicaciones dañado. No se sobrescribe; revisa o borra los datos locales.');
  if(new Set(data.map(e=>e.key)).size!==data.length)throw new Error('Historial con identificadores repetidos. No se sobrescribe.');
  return data.map(e=>({key:e.key,fingerprint:e.fingerprint,cn:e.cn,at:e.at,source:clean(e.source)}));
}
export function markNotified(rows,meta,confirmed,demo=false,storage=globalThis.localStorage){
  if(!confirmed)throw new Error('Confirma que la comunicación se ha realizado; preparar un borrador no la envía.');
  const ledger=loadLedger(demo,storage),map=new Map(ledger.map(e=>[e.key,e]));
  for(const r of rows)if(map.get(r.key)?.fingerprint!==r.fingerprint)map.set(r.key,{key:r.key,fingerprint:r.fingerprint,cn:r.cn,at:new Date().toISOString(),source:meta.title});
  if(map.size>2000)throw new Error('Máximo 2000 comunicaciones. Exporta el historial antes de limpiar datos.');
  storage.setItem(demo?KEYS.demo:KEYS.ledger,JSON.stringify([...map.values()]));
}
export function clear(storage=globalThis.localStorage){storage.removeItem(KEYS.ledger);storage.removeItem(KEYS.demo);}
export const STATUS={active:'Activa según fichero',resolved:'Resuelta según fichero',unknown:'Estado no informado o no reconocido'};
export const CHANGE={new:'Nueva en este historial',changed:'Modificada desde la última comunicación',notified:'Ya comunicada sin cambios'};
export function csv(report){
  const escape=v=>{let s=String(v??'');if(/^\s*[=+\-@]/.test(s)||/^[\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
  return '\uFEFF'+[['cn','nombre_catalogo','descripcion','inicio','fin_declarado','estado_segun_fichero','seguimiento','fuente','fecha_fichero'],...report.rows.map(r=>[r.cn,r.catalogNames,r.description,r.start,r.end,STATUS[r.status],CHANGE[r.change],report.source.title,report.source.date])].map(row=>row.map(escape).join(';')).join('\r\n');
}
export function mail(report,rows){
  return [`ASUNTO: Revisión de incidencias de suministro · fichero ${report.source.date}`,report.source.demo?'DEMOSTRACIÓN FICTICIA. No es una alerta AEMPS real.':'Borrador para revisión profesional. Datos del fichero aportado; no se ha consultado el estado actual en línea.',`Fuente declarada: ${report.source.title}\nFecha del fichero: ${report.source.date}\nReferencia: ${report.source.url||'Sin fuente real: demostración'}`,...rows.map(r=>`CN ${r.cn} · ${r.catalogNames}\n${r.description}\nInicio: ${r.start} · Fin declarado/previsto: ${r.end||'no aportado'}\n${STATUS[r.status]} · ${CHANGE[r.change]}`),'Comprueba la fuente oficial y el circuito de tu centro. Estas coincidencias no informan de existencias locales, sustituciones, financiación ni decisiones clínicas.','Este texto no se ha enviado. Registrar como comunicado requiere confirmación manual.'].join('\n\n');
}
