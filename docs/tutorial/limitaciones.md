# Limitaciones y registro de validación

- No es inventario, previsión de demanda, recomendación de sustitución ni sistema clínico certificado.
- No hay consulta en tiempo real, descarga automática o verificación remota de la fuente. Se exige fichero y referencia/fecha declaradas con revisión humana.
- Coincidir por CN no demuestra suministro actual. Ausencia o fin previsto no significan resolución. Estado no reconocido queda desconocido.
- No admite XLS antiguo, PDFs, fórmulas, macros ni todas las variantes Excel. Primera hoja: cabecera en la primera fila no vacía. Fechas no reconocidas deben ser texto ISO o DD/MM/AAAA.
- Códigos como texto de seis dígitos; no se reconstruye un CN perdido a partir de un nombre o número corto sin formato explícito.
- Historial local, editable, no cifrado y sin sincronizar; no prueba que un correo se haya enviado. Borrarlo puede causar duplicados.
- El borrador es texto y nunca se envía. Las comunicaciones requieren revisión y circuito institucional.
- Solo los ficheros de usuario pueden declararse como fuente AEMPS; las demostraciones están rotuladas como ficticias y usan historial separado.

## Resultados

Validación local realizada el 10 de noviembre de 2026:

- Node 24: 16 pruebas aprobadas, sin fallos ni omisiones; CSV, CN, fechas, duplicados, estados, identidad, cambios, fuente, deduplicación, cuota e historial.
- Chromium con Playwright: demostración inicial y actualizada, fuente/fecha/cobertura, ausencia no resuelta, nuevas/modificadas/comunicadas, confirmación separada y borrador sin envío: aprobados.
- XLSX almacenado y deflate, cadenas compartidas, formato CN 000000, fechas reconocidas, selección de columnas, rechazo de fórmulas/macros y CSV malformado: aprobados. Se usaron archivos ficticios generados con ZIP/XML estándar en el propio script, no datos reales de AEMPS.
- Texto con etiqueta HTML maliciosa conservado sin ejecución; CSV con fórmula neutralizada; exportaciones CSV/TXT/JSON comprobadas por contenido.
- Paginación de 55 filas, exportación de las 55 sin pérdida y selección por teclado: aprobados.
- Historial demo y real separados, persistencia tras recarga, borrado sin afectar a otra aplicación y error visible por historial dañado: aprobados. La cuota se prueba en Node.
- Controles etiquetados, tabla desplazable y anchuras 360, 390, 768 y 1440 px en aplicación y tutorial, sin desbordamiento de página; capturas revisadas.
- Seis pasos, documentos, prompts copiables, progreso/restablecimiento, enlaces locales bajo /farmastock/ y alternativa sin JavaScript: aprobados. Sin tráfico externo, errores JavaScript o respuestas HTTP fallidas durante los recorridos.
- Sintaxis YAML y empaquetado de Pages comprobados localmente. No equivale a ejecución alojada ni publicación.

No se probó la API oficial ni la autenticidad de un fichero real de AEMPS: el entorno bloqueó la consulta de su documentación. No se simula esa verificación. Una suite incompleta, un fichero descargado sin comprobar o una rama subida no demuestran funcionalidad ni publicación. No se afirma validación clínica, auditoría institucional, certificación de accesibilidad o compatibilidad con todos los libros Excel y navegadores.
