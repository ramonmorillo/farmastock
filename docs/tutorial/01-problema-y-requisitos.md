# 1. Del catálogo a las coincidencias revisables

FarmaStock Alert compara códigos nacionales de un catálogo con incidencias de un fichero aportado. No consulta inventario hospitalario ni disponibilidad real, no sugiere sustituciones y no toma decisiones clínicas.

## Criterios verificables

- Importar CSV UTF-8 o primera hoja XLSX con cabeceras y valores.
- Comparar exclusivamente CN de seis dígitos, sin aproximar nombres, completar ceros perdidos ni quitar dígitos de control.
- Conservar fuente, fecha, cobertura y estado aportado; exigir confirmación humana del origen y las columnas.
- Distinguir nueva para el historial, modificada y registrada como comunicada sin cambios.
- No resolver automáticamente por fin previsto ni por ausencia en otro fichero.
- Mantener estado desconocido cuando falta o no se reconoce la columna de estado.
- Preparar un borrador sin enviarlo; registrar comunicaciones solo mediante confirmación manual.
- Guardar únicamente el historial local y separar la demostración de los ficheros del usuario.

Las demostraciones son completamente ficticias: códigos, medicamentos e incidencias no se atribuyen a AEMPS. La fecha del fichero no se sustituye por la de hoy para aparentar actualidad.

Ejercicio: explica qué puedes y qué no puedes concluir si tu catálogo no tiene coincidencias en un listado parcial de incidencias. Una ausencia no prueba suministro normal ni stock disponible.
