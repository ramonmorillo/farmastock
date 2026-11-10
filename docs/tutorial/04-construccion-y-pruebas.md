# 4. Construcción y pruebas

## Módulos reales

- core.mjs: CSV, fechas, CN, normalización, duplicados, coincidencias, identidad/firma, historial y exportaciones.
- files.mjs: lector limitado de XLSX ZIP/OOXML sin dependencias, macros, fórmulas o relaciones externas.
- demos.mjs: catálogo y dos listados totalmente ficticios.
- app.mjs e index.html: ficheros, columnas, metadatos, revisión y borrador manual.
- stock.css: identidad reutilizada y tablas accesibles con desplazamiento local.
- tutorial.html y tutorial.mjs: seis pasos y lectura segura de docs.
- tests/core.test.mjs y scripts/test-farmastock.py: pruebas ejecutables.

```sh
npm test
npm run test:browser
git diff --check
```

Node usa su runner sin paquetes. El navegador requiere Playwright para Python y Chromium, disponibles en el entorno. No son dependencias de producción. En otro entorno prepara herramientas de desarrollo desde fuentes oficiales conservando TLS; usa CHROMIUM_PATH o chromium en PATH, o el navegador de Playwright.

El script genera sus XLSX con ZIP/XML estándar en una carpeta temporal fuera del checkout, prueba bajo /farmastock/ y comprueba exportaciones por contenido. No basta con ver una descarga ni con que no haya errores en consola.

## Depuración

CN corto: Excel puede haber perdido ceros; corrige el dato de origen, no lo deduzcas de un nombre. Fecha numérica: usa celdas de fecha reconocidas o texto ISO. Fórmula: exporta copia de valores para no usar caché obsoleta. Identidad repetida con contenido distinto: aporta un ID inequívoco o consolida. Historial dañado: no se sobrescribe. Importación fallida: corrígela antes de interpretar un resultado vacío.

Ejercicio: marca dos incidencias demo como comunicadas, carga el segundo listado y comprueba que una cambió, otra es nueva y una ausencia no se convierte en resolución.
