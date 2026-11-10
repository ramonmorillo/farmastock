# Arquitectura y decisiones · FarmaStock Alert v1

Se verificó ramonmorillo/farmastock, inicialmente vacío. Se prepararon main y feature/farmastock. Se reutilizan identidad visual, fuentes con licencias, lector de tutorial y workflows de las herramientas anteriores, sin modificar sus aplicaciones.

## Decisiones registradas

1. Sin backend, IA, credenciales ni telemetría. No se simula consulta actual de AEMPS: el entorno bloqueó la documentación API, por lo que se implementó importación manual revisada.
2. CSV UTF-8 y primera hoja XLSX, máximo 5 MB, 10 000 filas y 50 columnas. XLSX acotado: ZIP sin cifrar, métodos 0/8, CRC32, expansión máxima 20 MB y 10 MB por entrada; sin macros, fórmulas, relaciones externas o DTD. No es una biblioteca universal de Excel.
3. XLSX: cadenas compartidas/en línea, valores, formatos 000000 explícitos y fechas reconocidas (sistemas 1900/1904). No se evalúan fórmulas. Los formatos no reconocidos deben convertirse a texto antes de importar.
4. CN exacto de seis dígitos. No se añaden ceros perdidos salvo presentación explícita de la hoja, ni se quita control, compara por nombre o consulta inventario.
5. ID estable por CN+ID aportado o CN+inicio si no existe. Firma del contenido para detectar cambios; no es firma de autenticidad. Duplicados idénticos se consolidan; ambiguos se rechazan.
6. Estados activo, resuelto y desconocido proceden del fichero. Ni fin previsto ni ausencia resuelven nada automáticamente. La cobertura declarada se muestra y no se acredita con la importación.
7. ledger manual local para comunicadas. Preparar borrador no comunica ni modifica historial. Repetir una marca idéntica es idempotente. Demo y real usan claves separadas.
8. Los ficheros completos solo viven en memoria. Se conserva localmente únicamente el contenido de seguimiento confirmado, sin cifrar. Borrar el ledger pierde deduplicación y no borra exportaciones.
9. DOM seguro, CSV exportado con fórmulas neutralizadas, CSP sin conexiones. El tutorial lee documentos del mismo origen; el enlace a CIMA se abre por voluntad del usuario y nunca lleva el catálogo.
10. Rutas relativas bajo /farmastock/, despliegue independiente y solo la ficha del taller modificada tras publicación. No se copian contraseña, CNAME o materiales ajenos.

Código: core.mjs (motor), files.mjs (ficheros), demos.mjs (fixtures), app.mjs/index.html/stock.css (interfaz), tutorial.html/tutorial.mjs y docs/tutorial/ (guía), tests/ y scripts/ (pruebas), .github/workflows/ (CI/Pages).

Una URL oficial declarada no demuestra que los datos importados procedan de ella. El usuario debe verificar el original y no sustituir la fecha por hoy para simular actualidad.
