# Piloto de vigilancia por áreas · sin envío

Rama de trabajo: `feature/vigilancia-areas`. No modifica la aplicación publicada ni activa horarios diarios. No incluye transporte de correo.

## Resultado observado el 11 de noviembre de 2026

Desde GitHub Actions se obtuvo HTTP 200 para la página oficial, la API `/cima/rest/psuministro?pagina=1` y el PDF de documentación. La descarga paginada obtuvo 915 registros en cinco páginas de 200 como máximo. No debe confundirse ese número con nuevas incidencias de hoy, medicamentos distintos o incidencias de una sola área.

Se consultaron metadatos de una muestra no exhaustiva de 12 presentaciones: las dos primeras y otras diez seleccionadas por nombre únicamente para inspeccionar el esquema. El nombre NO determina la clasificación. El código ATC devuelto por CIMA permite proponer diez candidatas con códigos L01 a Oncología. La selección está sesgada deliberadamente para probar el circuito, no estima la cobertura. Los otros 905 registros quedan pendientes, incluidos los no enriquecidos y los que no tienen regla candidata.

Esta regla requiere revisión profesional: L01 no representa todo el trabajo de Oncología, y otras familias requieren reglas y excepciones específicas. Consultas externas no tiene regla por defecto: necesita una selección explícita de medicamentos, grupos o circuitos. No se asume que el resto pertenezca a esa área. Una presentación puede pertenecer a varias áreas.

La primera captura es una situación inicial, nunca novedades desde ayer. Las capturas posteriores permitirán comparar nuevas y modificadas; un registro ausente queda pendiente de revisión, no resuelto. La previsión de fin no garantiza reposición. En esta prueba no se han comparado dos capturas diarias ni verificado entregabilidad o condiciones de uso para producción. El PDF es accesible, pero falta revisar su contrato documentado antes del conector definitivo.

## Archivos y ejecución

- `scripts/vigilancia/probe.py`: consulta acotada de endpoints públicos, comprueba acceso y captura páginas/metadatos para inspección. Es un diagnóstico, no el conector de producción.
- `.github/workflows/cima-probe.yml`: ejecución manual o por cambios en estos dos archivos en la rama de prueba. Sin programación diaria; guarda únicamente respuestas públicas en una rama aislada y artefactos de siete días. Sin destinatarios ni secretos de correo.
- `scripts/vigilancia/preview.py`: valida integridad y paginación, exige coincidencia de CN en los metadatos y genera borradores privados. Un fallo de validación no produce un resumen vacío exitoso.
- `tests/vigilancia/test_preview.py`: pruebas sin conexión, sin correos reales.

Crear fuera del repositorio un directorio privado (modo 700), un fichero de destinatarios (600) y pasar las rutas:

```sh
python3 scripts/vigilancia/preview.py --report /ruta/privada/cima-probe.json --recipients /ruta/privada/recipients.json --out /ruta/privada/drafts.json
python3 -m unittest discover -s tests/vigilancia -v
npm test
```

Esquema de destinatarios con direcciones ficticias:

```json
{"oncologia":[{"email":"oncologia@example.invalid"}],"consultas-externas":[{"email":"externas@example.invalid"}]}
```

Las direcciones reales y los borradores con destinatarios nunca van a Git, Pages, logs ni artefactos públicos. La configuración local de este piloto no es un almacén permanente ni garantiza recuperación en otra sesión. Para activar envío faltan: reglas aprobadas, alcance completo de clasificación, histórico persistente y deduplicación, servicio de correo, gestión privada de destinatarios y autorización del propietario para el envío tras revisar los borradores. Descargar los datos correctamente no equivale a tener ya un servicio operativo diario.
