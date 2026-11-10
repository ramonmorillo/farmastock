# Prompts de auditoría y mejora

## Prompt de auditoría

```text
Audita FarmaStock sin cambiar otras herramientas. Ejecuta npm test y npm run
test:browser. Revisa CSV y XLSX, límites ZIP, fórmulas, fechas y ceros de CN.
Prueba filas inválidas, estados desconocidos y duplicados ambiguos. Exige
coincidencia exacta de CN, no aproximación por nombre. Comprueba que un fin
previsto pasado o una ausencia no resuelven una incidencia. Verifica historial
separado de demo, confirmación manual y que preparar correo no guarda ni envía.
Comprueba contenido de CSV/TXT/JSON, neutralización de fórmulas, XSS, móvil,
teclado, paginación y enlaces. Distingue aprobado, fallido y no ejecutado.
No elimines aserciones para ocultar errores. No publiques ni transmitas datos,
propongas sustituciones o añadas una API sin documentación verificada.
```

## Prompt de extensión

```text
En una rama implementa el reto de docs/tutorial/06-personalizacion.md.
Conserva la identidad CN+incidencia, firma de contenido y modo manual. Añade
una política revisable para alertas de estado desconocido, sin inferir stock
ni resolución por ausencia. Prueba una modificación posterior a comunicación,
la segunda lectura sin cambios y un fichero parcial. Registra límites y
resultados. No introduzcas envío automático ni credenciales de correo.
```
