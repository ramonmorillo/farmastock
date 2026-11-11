# Piloto de vigilancia por áreas · sin envío

La interfaz de importación publicada y los materiales existentes no se modifican. El piloto añade capturas públicas de prueba y revisiones locales privadas; no incluye transporte de correo.

## Funcionamiento

1. GitHub Actions consulta la página de CIMA, su API pública de problemas de suministro y la documentación. El acceso desde el entorno de desarrollo está bloqueado por su proxy; el acceso desde GitHub fue comprobado con HTTP 200.
2. El recolector descarga todas las páginas y rechaza listados incompletos, duplicados o inconsistentes. Consulta los metadatos de cada CN con dos trabajadores, pausas y reintentos limitados. Si CIMA devuelve HTTP 429, se detienen las solicitudes restantes hasta otra ejecución. La ejecución tiene un presupuesto de seis minutos: si se agota, conserva el resultado parcial y marca los CN sin verificar. Reutiliza metadatos de menos de siete días si coinciden CN y nombre, manteniendo su fecha original visible; el listado de suministro se vuelve a descargar siempre. Si faltan metadatos, el CN queda marcado para revisión, nunca omitido ni interpretado como ausencia de problemas. No se garantiza una captura atómica si CIMA cambia durante la descarga.
3. Se proponen áreas mediante reglas ATC versionadas y excepciones exactas. Se usa el nivel más específico para que el grupo padre no deshaga una excepción. Los nombres no deciden el área. Todas las reglas siguen **pendientes de aprobación profesional**.
4. Los borradores privados se agrupan por responsable, con una incidencia una sola vez aunque coincida con varias de sus áreas. Las filas muestran CN, presentación, estado, fechas, observaciones oficiales, cambio y motivo de asignación. Son revisables en navegador con filtro y teclado, sin dependencias ni consultas externas automáticas.
5. Opcionalmente se compara con una captura anterior validada: se suprimen los casos sin cambios, se distinguen cambios de estado explícitos y los registros ausentes se señalan para revisión. La primera captura es situación inicial, nunca novedades del día. Una fecha prevista no garantiza reposición.

## Áreas candidatas

| Área | Regla inicial para revisión |
|---|---|
| Infecciosas | J01, J02, J04, J05, P01, P02 |
| Neurología | N03, N04, N06D, N07XX, N02C; excepciones para interferones beta |
| Hipercolesterolemia | C10 |
| Oncohematología | L01, L02, L03AA, B02BD; excepciones para determinados inmunomoduladores |
| Inmunomediadas | L04AB, L04AC, L04AF; otras familias y calcineurínicos L04AD quedan para revisión |
| Pediatría | Solo asignaciones explícitas revisadas por CN, ninguna precargada |
| Resto pendiente | Bandeja de revisión organizativa; no es una especialidad inferida |

Estas reglas no cubren necesariamente todo el trabajo de cada área ni identifican la indicación real. El código ATC puede tener varios usos. Neurología no incluye por defecto todos los psicofármacos o analgésicos; Pediatría no se infiere del nombre, concentración, presentación ni un ATC. Las excepciones por CN permiten varias áreas. No se recomienda ninguna alternativa terapéutica.

## Archivos

- `scripts/vigilancia/probe.py`: recolector público acotado, validación de páginas, metadatos para todos los CN y resumen de errores.
- `scripts/vigilancia/rules.json`: reglas candidatas sin destinatarios.
- `scripts/vigilancia/preview.py`: comparación, asignación, deduplicación y generación local de HTML/JSON privados.
- `.github/workflows/cima-probe.yml`: ejecución manual de prueba y resultado exclusivamente público en rama separada, sin direcciones ni credenciales de correo.
- `tests/vigilancia/test_preview.py`: pruebas del motor, datos y privacidad.
- `scripts/vigilancia/test_browser.py`: navegador con datos ficticios, móvil, teclado, filtro, HTML literal y sin peticiones externas.

## Ejecutar borradores privados

Crear **fuera del repositorio** un directorio de modo 700. Guardar las asignaciones en un JSON privado de modo 600, usando esta estructura (direcciones ficticias):

```json
{
  "mode": "preview-no-delivery",
  "assignments": [
    {"recipient": {"name": "Responsable 1", "email": "uno@example.invalid"}, "areas": ["infecciosas", "neurologia", "hipercolesterolemia"]},
    {"recipient": {"name": "Responsable 2", "email": "dos@example.invalid"}, "areas": ["oncohematologia"]},
    {"recipient": {"name": "Responsable 3", "email": "tres@example.invalid"}, "areas": ["inmunomediadas", "pediatria", "resto-pendiente-de-clasificacion"]}
  ]
}
```

```sh
python3 scripts/vigilancia/preview.py --report /ruta/cima-probe.json --assignments /privado/assignments.json --out-dir /privado/borradores
# Añadir --previous /ruta/captura-anterior.json para comparar dos capturas.
python3 -m unittest discover -s tests/vigilancia -v
python3 scripts/vigilancia/test_browser.py
npm test
```

Los HTML no incluyen direcciones, no envían correos ni cargan recursos externos. El JSON privado sí contiene destinatarios para el futuro transporte. El generador rechaza salidas dentro del checkout o directorios sin permisos privados, y no sigue enlaces simbólicos en los archivos de salida. Las direcciones reales no están en Git, Pages, logs ni artefactos públicos. La configuración temporal local no es almacenamiento permanente ni garantiza recuperación en otra sesión.

## Lo que falta para operar diariamente

Revisar y completar reglas con el servicio; confirmar el contrato documentado y las condiciones de uso de CIMA; validar varias capturas a lo largo de días; definir frecuencia y avisos relevantes; disponer de configuración privada persistente y servicio de correo con remitente verificado, resultados de envío y deduplicación duradera. El primer paso seguirá siendo modo sin envío. Activar correos requiere que el propietario revise los borradores y autorice el envío: los contactos facilitados para esta prueba no implican envío autorizado.

Los resultados públicos se guardan como puntos de control durante la descarga para facilitar el diagnóstico; su recuperación tras un timeout depende de que el runner alcance la subida de artefactos.

El workflow de descarga queda manual para evitar repetir cientos de solicitudes con cada cambio de código. La CI del motor sí se ejecuta con los cambios de la rama.

Las pruebas locales no equivalen a validación clínica, aprobación institucional ni comprobación de entregabilidad.

## Resultado de la prueba acotada del 11/11/2026

El intento completo agotó 25 minutos sin terminar. La versión acotada finalizó en 6 min 31 s: listado completo de 911 registros activos y metadatos verificados para 248 CN, incluyendo 12 reutilizados de la captura de la mañana; 663 CN quedaron pendientes por presupuesto de tiempo. No hubo errores HTTP observados en las consultas terminadas. No se afirma clasificación completa ni vigilancia diaria operativa.

La inspección real encontró ciclosporina y tacrolimus en el grupo amplio L04 inicialmente candidato a Inmunomediadas. La versión v2 elimina esa asignación general: los usos compartidos, incluidos los de trasplante, pasan a revisión. Pediatría sigue sin inferirse automáticamente. Los resúmenes privados y la comparación con la captura de la mañana se generan fuera del repositorio; no son envíos.

## Carga inicial reanudable y observación diaria

`scripts/vigilancia/batches.py` ejecuta hasta seis lotes de seis minutos, reutiliza la caché y conserva cada avance en la rama de datos mediante commits normales, sin reescribir el histórico. Detiene la secuencia al completar la cobertura, recibir HTTP 429, agotar los lotes o comprobar falta de progreso. Nunca declara completa una captura sin metadatos verificables para cada CN actual. Los errores no reemplazan una captura válida con una lista vacía.

`.github/workflows/cima-daily-pilot.yml` programa dos ventanas UTC (06:10 y 07:10); `daily.py` permite una captura por día local a partir de las 08:00 de Europe/Madrid. Esto cubre invierno y verano aproximadamente a las 08:10. GitHub puede retrasar las ejecuciones: siempre se conserva la hora real. La segunda ventana se omite si ya existe una captura del día. Una ejecución manual explícita puede forzar otra captura de prueba. No se han observado todavía varios días consecutivos; la programación habilita esa comprobación futura. Los destinatarios no se cargan en GitHub.

`review.py` selecciona hasta tres ejemplos por área, procurando distintos ATC, y hasta cuatro casos dudosos con metadatos verificados. Conserva la clasificación pendiente de los usos compartidos, retira direcciones del material descargable y permite exportar decisiones en JSON local. No sube decisiones, no modifica reglas y no activa envíos. Las muestras no sustituyen al listado completo y no se usan para estimar incidencias por área.

```sh
python3 scripts/vigilancia/review.py --drafts /privado/drafts.json --report /ruta/cima-probe.json --out-dir /privado/revision-breve
python3 scripts/vigilancia/test_review_browser.py
```

La activación de correo sigue pendiente de la revisión profesional, un remitente verificado, un servicio de envío y autorización posterior. La captura diaria de datos públicos no equivale a un servicio de avisos en producción.

## Carga completada el 11/11/2026

La carga reanudable completó tres lotes, conservando cada avance: 550, 678 y 911 CN verificados. La captura final del listado se inició a las 17:27 de Europe/Madrid y los metadatos terminaron a las 17:32. Los 911 CN actuales tienen respuesta verificable con pertenencia a la presentación consultada; faltantes técnicos: cero. Esto no significa que todos tengan una especialidad asignada.

Reglas v2: Infecciosas 85, Neurología 53, Hipercolesterolemia 22, Oncohematología 101, Inmunomediadas 3; Pediatría sin asignaciones explícitas. Quedan 647 incidencias sin regla de área, en revisión clínica. No se confunden con metadatos pendientes. Las propuestas no demuestran la indicación de un medicamento ni su uso en un hospital concreto.

Las muestras breves contienen nueve ejemplos para el primer responsable, tres para Oncohematología y seis para la tercera responsable (dos ATC distintos de Inmunomediadas y cuatro casos dudosos). No incluyen direcciones reales y no ejecutan ninguna comunicación. La comparación con la captura de las 11:51 muestra 911 registros sin cambios y cuatro registros ausentes, que requieren revisión y no se declaran resueltos.

La programación de captura diaria está incorporada a main, solo para datos públicos y sin correos. La primera observación entre días será posterior a esta entrega; las pruebas de calendario verifican invierno, verano y deduplicación por fecha local, sin fingir que ya se observaron varios días reales.
