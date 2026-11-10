export const DEMO={
  catalog:'cn;nombre\n000001;Medicamento ficticio A\n000002;Medicamento ficticio B\n000003;Medicamento ficticio C',
  first:'id;cn;inicio;fin;descripcion;estado\nDEMO-A;000001;2026-01-01;2026-01-10;Incidencia totalmente ficticia A;activa\nDEMO-B;000002;2026-01-02;;Incidencia totalmente ficticia B;desconocido\nDEMO-C;000003;2026-01-03;;Incidencia ficticia ya resuelta;resuelta\nDEMO-X;999999;2026-01-04;;Fuera del catálogo ficticio;activa',
  changed:'id;cn;inicio;fin;descripcion;estado\nDEMO-A;000001;2026-01-01;2026-01-20;Incidencia ficticia A con actualización;activa\nDEMO-C;000003;2026-01-03;;Incidencia ficticia ya resuelta;resuelta\nDEMO-D;000002;2026-01-05;;Nueva incidencia ficticia D;activa',
};
export function demoMeta(){return {title:'Listado de demostración: no procede de AEMPS',date:'2026-01-06',url:'',scope:'partial',demo:true};}
