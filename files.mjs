// Lector acotado de CSV y primera hoja XLSX. No ejecuta fórmulas, macros o enlaces.
import {parseCSV,table} from './core.mjs';
const decoder=new TextDecoder('utf-8',{fatal:true});
function xml(bytes){const s=decoder.decode(bytes);if(/<!DOCTYPE|<!ENTITY/i.test(s))throw new Error('No se admiten DTD o entidades XML.');const doc=new DOMParser().parseFromString(s,'application/xml');if(doc.getElementsByTagName('parsererror').length)throw new Error('XML del XLSX no válido.');return doc;}
const all=(node,name)=>[...node.getElementsByTagNameNS('*',name)];
function crc32(bytes){let c=0xffffffff;for(const b of bytes){c^=b;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;}
async function unzip(buffer){
  const bytes=new Uint8Array(buffer),v=new DataView(buffer);let end=-1;
  for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--)if(v.getUint32(i,true)===0x06054b50){end=i;break;}
  if(end<0)throw new Error('El fichero no es un XLSX ZIP válido.');
  if(v.getUint16(end+4,true)||v.getUint16(end+6,true))throw new Error('ZIP dividido no compatible.');
  const count=v.getUint16(end+10,true);let offset=v.getUint32(end+16,true),total=0;const entries=new Map();
  if(count>1000)throw new Error('XLSX con demasiados archivos.');
  for(let i=0;i<count;i++){
    if(offset+46>bytes.length||v.getUint32(offset,true)!==0x02014b50)throw new Error('Directorio ZIP inválido.');
    const flags=v.getUint16(offset+8,true),method=v.getUint16(offset+10,true),crc=v.getUint32(offset+16,true),compressed=v.getUint32(offset+20,true),size=v.getUint32(offset+24,true),nameLength=v.getUint16(offset+28,true),extra=v.getUint16(offset+30,true),comment=v.getUint16(offset+32,true),local=v.getUint32(offset+42,true);
    if(offset+46+nameLength+extra+comment>bytes.length)throw new Error('ZIP truncado.');
    const name=decoder.decode(bytes.slice(offset+46,offset+46+nameLength));total+=size;
    if(flags&1||![0,8].includes(method)||size>10000000||total>20000000||compressed===0xffffffff||name.split('/').includes('..')||name.startsWith('/')||entries.has(name))throw new Error('XLSX cifrado, duplicado, demasiado grande o no compatible.');
    if(/vbaProject|externalLinks/i.test(name))throw new Error('No se admiten macros ni vínculos externos. Exporta una copia de valores.');
    entries.set(name,{method,crc,compressed,size,local});offset+=46+nameLength+extra+comment;
  }
  return async name=>{
    const e=entries.get(name);if(!e)throw new Error(`Falta ${name} en el XLSX.`);
    if(e.local+30>bytes.length||v.getUint32(e.local,true)!==0x04034b50)throw new Error('Cabecera ZIP inválida.');
    const start=e.local+30+v.getUint16(e.local+26,true)+v.getUint16(e.local+28,true);if(start+e.compressed>bytes.length)throw new Error('Datos ZIP truncados.');
    let output=bytes.slice(start,start+e.compressed);
    if(e.method===8){
      const reader=new Blob([output]).stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader(),chunks=[];let length=0;
      try{while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>e.size||length>10000000){await reader.cancel();throw new Error('XLSX expandido supera su límite.');}chunks.push(value);}}
      finally{reader.releaseLock();}
      output=new Uint8Array(length);let position=0;for(const chunk of chunks){output.set(chunk,position);position+=chunk.length;}
    }
    if(output.length!==e.size||crc32(output)!==e.crc)throw new Error('Comprobación de integridad ZIP fallida.');return output;
  };
}
export async function parseXLSX(buffer){
  const read=await unzip(buffer),workbook=xml(await read('xl/workbook.xml')),rels=xml(await read('xl/_rels/workbook.xml.rels'));
  const sheet=all(workbook,'sheet')[0];if(!sheet)throw new Error('El libro no tiene hojas.');
  const rid=sheet.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships','id')||sheet.getAttribute('r:id');
  const relationships=all(rels,'Relationship');if(relationships.some(r=>r.getAttribute('TargetMode')==='External'))throw new Error('No se admiten relaciones externas.');
  const relation=relationships.find(r=>r.getAttribute('Id')===rid);if(!relation)throw new Error('Relación de hoja no encontrada.');
  const path=new URL(relation.getAttribute('Target'),'https://xlsx.invalid/xl/').pathname.slice(1);if(!path.startsWith('xl/'))throw new Error('Ruta de hoja no compatible.');
  const data=xml(await read(path));if(all(data,'f').length)throw new Error('La hoja contiene fórmulas. Exporta valores para no usar resultados almacenados potencialmente obsoletos.');
  let strings=[],styles=[],formats=new Map();
  try{strings=all(xml(await read('xl/sharedStrings.xml')),'si').map(si=>all(si,'t').map(t=>t.textContent).join(''));}catch(e){if(!e.message.startsWith('Falta '))throw e;}
  try{const doc=xml(await read('xl/styles.xml'));formats=new Map(all(doc,'numFmt').map(n=>[Number(n.getAttribute('numFmtId')),n.getAttribute('formatCode')]));const cellXfs=all(doc,'cellXfs')[0];styles=cellXfs?all(cellXfs,'xf').map(n=>Number(n.getAttribute('numFmtId'))):[];}catch(e){if(!e.message.startsWith('Falta '))throw e;}
  const epoch1904=all(workbook,'workbookPr')[0]?.getAttribute('date1904');const alternate=epoch1904==='1'||epoch1904==='true';
  const rows=[];
  for(const row of all(data,'row')){
    if(rows.length>=10001)throw new Error('Máximo 10 000 filas.');const values=[];
    for(const cell of all(row,'c')){
      const reference=cell.getAttribute('r')||'',letters=reference.match(/^([A-Z]+)\d+$/)?.[1];if(!letters)throw new Error('Referencia de celda no válida.');
      let col=0;for(const c of letters)col=col*26+c.charCodeAt(0)-64;col--;if(col>=50)throw new Error('Máximo 50 columnas.');
      const type=cell.getAttribute('t');let value=all(cell,'v')[0]?.textContent||'';
      if(type==='s'){if(!/^\d+$/.test(value)||strings[Number(value)]===undefined)throw new Error('Referencia de texto XLSX no válida.');value=strings[Number(value)];}
      else if(type==='inlineStr')value=all(cell,'t').map(n=>n.textContent).join('');
      else if(type==='e')throw new Error('La hoja contiene errores de Excel.');
      else if(type==='d')value=value.slice(0,10);
      else if((!type||type==='n')&&value){
        const formatId=styles[Number(cell.getAttribute('s')||0)],format=formats.get(formatId)||'';
        if([14,15,16,17,22].includes(formatId)||/[dy]/i.test(format.replace(/"[^"]*"|\[[^\]]*\]|\\./g,''))){
          const serial=Number(value);if(!Number.isFinite(serial)||serial<0||(!alternate&&serial<61)||serial>100000)throw new Error('Fecha Excel fuera del rango compatible.');
          value=new Date(Date.UTC(alternate?1904:1899,alternate?0:11,alternate?1:30)+Math.floor(serial)*86400000).toISOString().slice(0,10);
        }else if(format==='000000'&&/^\d{1,6}$/.test(value))value=value.padStart(6,'0');
      }
      if(value.length>12000)throw new Error('Celda demasiado extensa.');values[col]=value;
    }
    rows.push(Array.from({length:values.length},(_,i)=>values[i]||''));
  }
  return {...table(rows),sheet:sheet.getAttribute('name')};
}
export async function readFile(file){
  if(file.size>5000000)throw new Error('Máximo 5 MB por fichero.');
  if(/\.csv$/i.test(file.name)){const text=await file.text();if(text.includes('\u0000'))throw new Error('Exporta el CSV como UTF-8, sin caracteres nulos.');return {...parseCSV(text),sheet:''};}
  if(/\.xlsx$/i.test(file.name))return parseXLSX(await file.arrayBuffer());
  throw new Error('Usa CSV o XLSX (primera hoja, sin fórmulas, macros o vínculos externos).');
}
