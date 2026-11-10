# 3. Encargo y especificación reproducible

## Encargo real

«perfecto vamos a por la tercera herramienta farmasotck alert, creo el repo de farmastock»; posteriormente: «ya esta creado».

La ficha del taller proponía comparar un catálogo con problemas de suministro AEMPS, importar Excel/CSV y preparar alertas revisables, con el reto de distinguir nuevas de ya comunicadas. La especificación siguiente concreta esa necesidad para reproducir esta versión; no es una falsa transcripción de otro agente ni una certificación institucional.

## Prompt reproducible

```text
Construye FarmaStock Alert y tutorial en ramonmorillo/farmastock. Inspecciona
archivos, conserva cambios ajenos y no modifiques otras herramientas.
Web estática modular, sin backend, claves, IA, telemetría o correo automático.
Importa CSV UTF-8 y primera hoja XLSX, sin fórmulas, macros o enlaces externos.
Limita tamaños, filas, expansión ZIP y comprueba integridad. No interpretes
HTML ni ejecutes contenido de las hojas. Asocia columnas explícitamente.
Compara CN de seis dígitos exactamente. No uses nombres aproximados ni
reconstruyas códigos que Excel perdió, salvo un formato explícito 000000.
Conserva ID oficial si existe, inicio, fin declarado, descripción y estado.
Si falta estado queda desconocido; un fin previsto pasado no resuelve.
Registra fuente oficial HTTPS declarada, fecha y cobertura. Exige revisión
humana. No confundas la URL con autenticación del contenido importado.
Sin documentación API verificada no inventes una conexión en vivo: admite
ficheros descargados y revisados por el usuario con referencia AEMPS/CIMA.
Identidad estable: CN+ID de incidencia o CN+inicio sin ID. Cambios de contenido,
estado o fin previsto generan una versión modificada. Rechaza IDs ambiguos.
Historial manual local y sin cifrar para nueva/modificada/comunicada. Preparar
un correo no lo envía ni lo registra como enviado. Exige confirmación separada.
Una fila ausente no se trata como resuelta. Separa historial demo y real.
Importaciones erróneas no producen un falso resultado sin alertas. Al cambiar
datos, columnas o metadatos invalida el informe y su revisión anterior.
Exporta revisión CSV neutralizando fórmulas, borrador TXT y copia JSON del
historial. No almacenes los ficheros completos ni datos de pacientes.
Demostración completamente ficticia y segundo fichero con cambios y ausencia.
Interfaz móvil, teclado, etiquetas, foco, mensajes, tablas desplazables y
paginación sin perder filas en la exportación. Rutas bajo /farmastock/.
Tutorial de seis pasos con documentos y prompts copiables. Pruebas Node y
navegador de CSV/XLSX, datos inválidos, cambios, duplicados, ausencia, correo
manual, persistencia, privacidad, XSS, exportaciones, teclado y móvil.
Prepara Pages y cambia solo la ficha del taller tras comprobar despliegue.
Conserva contraseña, materiales y otras herramientas. Informa pruebas no
realizadas y no inventes resultados remotos o verificación científica.
```

Funcional: lectura, comparación y seguimiento. Técnico: esquema, identidad, fichero y ledger. Visual: tabla y revisión. Seguridad: no falsos negativos, origen declarado, no envío y exportación saneada. Verifica cada grupo con una aserción que pueda fallar.
