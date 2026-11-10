import test from 'node:test';
import assert from 'node:assert/strict';
import {cn,date,parseCSV,table,suggest,catalog,incidents,status,analyze,validateSource,identity,signature,loadLedger,markNotified,clear,csv,mail,KEYS} from '../core.mjs';
import {DEMO,demoMeta} from '../demos.mjs';
const cm={cn:0,name:1},im={id:0,cn:1,start:2,end:3,description:4,status:5};
function setup(updated=false){return {c:catalog(parseCSV(DEMO.catalog),cm),i:incidents(parseCSV(updated?DEMO.changed:DEMO.first),im),meta:demoMeta()};}
class Storage{data=new Map();getItem(k){return this.data.get(k)??null;}setItem(k,v){this.data.set(k,String(v));}removeItem(k){this.data.delete(k);}}
test('CSV: BOM, separadores, comillas escapadas, saltos de línea y CN con ceros',()=>{
  const t=parseCSV('\uFEFFcn;nombre\r\n000001;"Nombre; con ""comillas""\ny salto"\r\n');
  assert.equal(t.rows[0][0],'000001');assert.equal(t.rows[0][1],'Nombre; con "comillas"\ny salto');
  assert.deepEqual(parseCSV('cn,nombre\n000001,Prueba').rows,[['000001','Prueba']]);
});
test('CSV malformado, vacío, cabeceras ambiguas y filas extensas se rechazan',()=>{
  for(const text of ['','cn;nombre\n','cn;cn\n000001;x','cn;nombre\n000001;"sin cierre','cn;nombre\n000001;"x"invalido','cn;nombre\n000001;x;extra'])assert.throws(()=>parseCSV(text));
  assert.throws(()=>parseCSV('cn;nombre\n000001;'+ 'a'.repeat(12001)),/extensa/);
});
test('CN exacto: sin inferir ceros, controles, códigos de barras o nombres similares',()=>{
  assert.equal(cn(' 000001 '),'000001');for(const bad of ['1','1234567','123456.7','CN123456','12345x'])assert.throws(()=>cn(bad));
  assert.equal(suggest(['Código nacional','Nombre'],'cn'),0);
});
test('Fechas estrictas, equivalencia de formatos e imposibles',()=>{
  assert.equal(date('02/01/2026'),'2026-01-02');assert.equal(date('',true),'');
  for(const bad of ['2026-02-30','31/04/2026','46024','2026-1-2'])assert.throws(()=>date(bad));
});
test('Catálogo: consolida duplicados exactos y conserva denominaciones distintas',()=>{
  const result=catalog(parseCSV('cn;nombre\n000001;A\n000001;A\n000001;Alias'),cm);assert.equal(result.duplicates,1);assert.deepEqual(result.items[0].names,['A','Alias']);
  assert.throws(()=>catalog(parseCSV('cn;nombre\n1;A'),cm),/fila 2/);
});
test('Estado desconocido permanece pendiente; un fin previsto pasado no resuelve',()=>{
  for(const value of ['','DESCONOCIDO','cualquier otro texto'])assert.equal(status(value),'unknown');
  assert.equal(status('Sí'),'active');assert.equal(status('0'),'resolved');
  const {i}=setup();assert.equal(i.items[0].status,'active');assert.equal(i.items[0].end,'2026-01-10');
});
test('Incidencias: no ignora filas inválidas, conflictos o fechas incoherentes',()=>{
  const t=parseCSV(DEMO.first);t.rows[0][2]='2026-02-30';assert.throws(()=>incidents(t,im),/fila 2/);
  const x=parseCSV(DEMO.first);x.rows.push([...x.rows[0]]);assert.equal(incidents(x,im).duplicates,1);x.rows.at(-1)[4]='Contenido distinto';assert.throws(()=>incidents(x,im),/repetido/);
  const y=parseCSV(DEMO.first);y.rows[0][3]='2025-01-01';assert.throws(()=>incidents(y,im),/anterior/);
});
test('Identidad por ID o CN+inicio y firma que detecta contenido/estado/fin modificado',()=>{
  const {i}=setup(),r=i.items[0];assert.equal(identity(r),identity({...r,description:'otra'}));assert.notEqual(signature(r),signature({...r,description:'otra'}));
  assert.equal(signature(r),signature({...r,rawStatus:'1'}));
  assert.notEqual(identity({...r,id:''}),identity({...r,id:'',start:'2026-01-02'}));
});
test('Fuente: fecha, referencia oficial HTTPS, cobertura y demo explícita',()=>{
  assert.equal(validateSource(demoMeta()).demo,true);
  const m={...demoMeta(),demo:false,url:'https://cima.aemps.es/cima/publico/home.html'};assert.equal(validateSource(m).date,'2026-01-06');
  for(const url of ['https://aemps.es.attacker.com/','http://aemps.es','javascript:alert(1)','https://user:pass@cima.aemps.es'])assert.throws(()=>validateSource({...m,url}));
  assert.throws(()=>validateSource({...m,date:'2099-01-01'}),/futuro/);
});
test('Comparación por CN, sin coincidencia por nombre ni consulta de stock',()=>{
  const {c,i,meta}=setup(),r=analyze(c.items,i.items,meta);assert.equal(r.rows.length,3);assert.equal(r.unmatched,1);assert.ok(r.rows.every(r=>r.change==='new'));
  assert.equal(analyze([{cn:'888888',names:['Medicamento ficticio A']}],i.items,meta).rows.length,0);
});
test('No se registra comunicación sin confirmación y preparar correo no guarda nada',()=>{
  const s=new Storage(),{c,i,meta}=setup(),r=analyze(c.items,i.items,meta);
  assert.match(mail(r,r.rows.slice(0,1)),/no se ha enviado/i);assert.equal(loadLedger(true,s).length,0);
  assert.throws(()=>markNotified(r.rows,meta,false,true,s),/Confirma/);
});
test('Nuevas, comunicadas y modificadas; marca idempotente y ausencia no resuelta',()=>{
  const s=new Storage(),{c,i,meta}=setup(),r=analyze(c.items,i.items,meta);
  markNotified(r.rows.slice(0,2),meta,true,true,s);const before=loadLedger(true,s);
  assert.equal(analyze(c.items,i.items,meta,before).rows.filter(r=>r.change==='notified').length,2);
  markNotified(r.rows.slice(0,2),meta,true,true,s);assert.deepEqual(loadLedger(true,s),before);
  const updated=setup(true),next=analyze(c.items,updated.i.items,meta,before);
  assert.equal(next.rows.find(r=>r.id==='DEMO-A').change,'changed');assert.equal(next.rows.find(r=>r.id==='DEMO-D').change,'new');assert.equal(next.notObserved.length,1);assert.equal(next.notObserved[0].cn,'000002');
});
test('Historial demo separado del real y borrado limitado a FarmaStock',()=>{
  const s=new Storage();s.setItem('otra-app','conservar');const {c,i,meta}=setup(),r=analyze(c.items,i.items,meta);markNotified(r.rows,meta,true,true,s);assert.equal(loadLedger(false,s).length,0);clear(s);assert.equal(loadLedger(true,s).length,0);assert.equal(s.getItem('otra-app'),'conservar');
});
test('Historial dañado y cuota: no se sobrescriben comunicaciones anteriores',()=>{
  const s=new Storage();s.setItem(KEYS.demo,'roto');assert.throws(()=>loadLedger(true,s));assert.equal(s.getItem(KEYS.demo),'roto');
  const {c,i,meta}=setup(),r=analyze(c.items,i.items,meta);assert.throws(()=>markNotified(r.rows,meta,true,true,{getItem:()=>null,setItem:()=>{throw new Error('QuotaExceededError');}}),/Quota/);
});
test('CSV exportado conserva CN, fuente, fecha y neutraliza fórmulas',()=>{
  const {c,i,meta}=setup(),r=analyze(c.items,i.items,meta);r.rows[0].description='=HYPERLINK("https://example.org")';r.rows[1].catalogNames='@SUM(1)';
  const exported=csv(r),parsed=parseCSV(exported);assert.equal(parsed.rows[0][0],'000001');assert.ok(parsed.rows[0][2].startsWith("'="));assert.ok(parsed.rows[1][1].startsWith("'@"));assert.ok(exported.includes(meta.title));
});
test('La fuente sin columna de estado no se interpreta como resuelta o normal',()=>{
  const t=parseCSV(DEMO.first),r=incidents(t,{...im,status:-1});assert.ok(r.items.every(r=>r.status==='unknown'));
});
