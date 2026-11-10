# 5. Auditoría y publicación

Revisa códigos y fechas, columnas, todas las filas inválidas, duplicados y falta de estado. Confirma que no hay coincidencias por nombre ni inferencias de stock. Comprueba CSV exportado con una celda que empieza por = y que las fórmulas de XLSX se rechacen. Ejecuta ambos comandos de pruebas y el prompt de auditoría.

## GitHub Pages

Repositorio https://github.com/ramonmorillo/farmastock, sin CNAME. Las rutas son relativas y la aplicación se prueba bajo /farmastock/.

1. Settings → Pages → Source: GitHub Actions.
2. Fusiona el desarrollo revisado a main.
3. pages.yml ejecuta npm test, prepara aplicación, módulos, assets y docs y publica.
4. Comprueba SHA, ejecución y URL efectiva. La dirección prevista es https://ramonmorillo.github.io/farmastock/ y puede heredar ramonmorillo.es conservando el prefijo.
5. Prueba demostración, listado actualizado, revisión y tutorial antes de publicar los enlaces del taller.

ci.yml ejecuta Node en push y PR; el navegador se ejecuta aparte. Activar Pages por primera vez puede requerir un ajuste administrativo del propietario. No confundas una rama subida o una CI verde con una aplicación publicada.

El cifrado de Santiago permanece en el repositorio de la web. Cambia solo la ficha FarmaStock y regenera solo Santiago con la clave actual. No copies claves ni materiales aquí; la aplicación pública no hereda ese acceso.

Ejercicio: identifica una ejecución de Pages y compara su SHA con la versión probada. Registra qué se comprobó localmente y qué en remoto.
