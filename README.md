# FarmaStock Alert

Compara un catálogo hospitalario con incidencias de suministro de un fichero aportado y prepara comunicaciones revisables. No consulta stock, propone sustituciones ni verifica disponibilidad actual.

## Qué incluye

- CSV UTF-8 y primera hoja XLSX, con selección explícita de columnas.
- Coincidencia exacta por CN de seis dígitos, conservando ceros; sin aproximar nombres.
- Fuente, fecha y cobertura declaradas, con revisión humana antes de comparar.
- Estados activos, resueltos o desconocidos según el fichero; no se infiere resolución por fecha prevista o ausencia.
- Incidencias nuevas para el historial, modificadas y registradas como comunicadas sin cambios.
- Historial local separado para demostración; marcado idempotente y revisión ante cambios desde otra pestaña.
- Borrador editable TXT/portapapeles, nunca correo automático; registro de comunicación con confirmación separada.
- Exportación CSV con fórmulas neutralizadas e historial JSON.
- Demostración ficticia y un segundo fichero con cambios y ausencias.
- Tutorial de seis pasos, documentos y prompts copiables.

## Ejecutar y comprobar

Node.js 24 y Python 3, sin paquetes npm, backend, claves o compilación.

```sh
git clone https://github.com/ramonmorillo/farmastock.git
cd farmastock
npm run serve
```

Abre la raíz del servidor y tutorial.html, no file://. La versión inicial está incorporada a main; para mejoras posteriores crea una rama y abre una PR. Las rutas relativas funcionan bajo /farmastock/.

```sh
npm test
npm run test:browser
```

Node usa su runner sin dependencias. El script Python requiere Playwright y Chromium y crea sus XLSX de prueba con la biblioteca estándar, sin descargar ficheros ni paquetes de hojas de cálculo. Artefactos temporales fuera del checkout. Resultados en docs/tutorial/limitaciones.md.

## Circuito de uso

1. Carga demo o catálogo y listado de incidencias que hayas obtenido y contrastado por separado en la fuente oficial.
2. Revisa columnas, fecha, referencia y cobertura. La URL oficial declarada no autentica el contenido del fichero.
3. Compara, contrasta las coincidencias y selecciona las incidencias revisadas.
4. Prepara el borrador; no se envía ni se marca automáticamente como comunicado.
5. Solo tras la comunicación realizada por tu circuito habitual, confirma y registra la selección.
6. En la siguiente lectura, los cambios se vuelven a revisar. Una incidencia ausente no se transforma en resuelta.

CN debe ser texto de seis dígitos. No se reconstruyen ceros perdidos salvo que el formato XLSX explícito 000000 los conserve. No se quitan controles ni barras. Los estados desconocidos no equivalen a ausencia de problemas.

## Formatos y límites

Máximo 5 MB por fichero, 10 000 filas y 50 columnas. XLSX: primera hoja, primera fila no vacía como cabecera, valores y fechas reconocidas, sin fórmulas, macros, vínculos externos o libros cifrados. No es un lector universal de Excel; usa CSV UTF-8 o una copia de valores si tu formato no es compatible. No admite XLS antiguo o PDF.

## Publicar

Settings → Pages → Source: GitHub Actions. Al incorporar a main, pages.yml ejecuta pruebas, empaqueta aplicación/assets/docs y publica. ci.yml ejecuta Node en push y PR; el navegador se ejecuta aparte. Sin CNAME.

Publicación confirmada por GitHub Pages: **https://ramonmorillo.es/farmastock/**. Tutorial: **https://ramonmorillo.es/farmastock/tutorial.html**. El proyecto conserva /farmastock/ bajo el dominio del propietario; comprueba cada nuevo despliegue antes de anunciarlo. Una rama subida no significa publicación.

## Límites y privacidad

La aplicación web de importación manual no consulta la API: usa una importación revisada y fechada. El piloto de vigilancia CIMA se ejecuta por separado, como se describe más abajo. Los ficheros solo se procesan en memoria. El historial confirmado conserva localmente información de seguimiento, sin cifrar ni sincronizar, y no es prueba de envío ni auditoría inmutable. Borrarlo pierde deduplicación. Los archivos exportados y el portapapeles se borran aparte.

Sin datos de pacientes, IA, telemetría o credenciales. La aplicación es pública, no hereda la clave del taller y no es un producto sanitario certificado. La validación profesional e institucional es independiente de las pruebas técnicas.

## Estructura

core.mjs: comparación e historial; files.mjs: CSV/XLSX acotado; demos.mjs: ejemplos ficticios; app.mjs/index.html/stock.css: interfaz; tutorial.html/tutorial.mjs y docs/tutorial/: guía; tests/ y scripts/: pruebas; .github/workflows/: CI/Pages. Procedencia y licencias en NOTICE.md y assets/fonts/.

## Piloto CIMA por áreas · sin envío

El piloto descarga datos públicos de CIMA, completa los metadatos por lotes reanudables y genera revisiones breves por áreas sin catálogo local. La captura diaria de prueba se configura mediante `cima-daily-pilot.yml`; el código no contiene servicio de correo, credenciales ni destinatarios reales. La interfaz de importación y los materiales docentes existentes se conservan.

Las reglas ATC son propuestas pendientes de revisión profesional. Pediatría no se infiere automáticamente. La configuración de responsables y los borradores se mantienen fuera del repositorio. Véase [documentación del piloto](docs/vigilancia/PRUEBA.md).
