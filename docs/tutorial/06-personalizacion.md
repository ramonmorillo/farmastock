# 6. Personalización y reto

Asocia las columnas a CN, nombre de catálogo, ID de incidencia opcional, inicio, fin declarado opcional, descripción y estado. No alteres el significado de las columnas para que pase una validación. Los CN deben tener seis dígitos sin control ni barras; conserva texto o formato explícito 000000 en Excel.

Estados reconocidos: activo/activa/en curso/sí/true/1 y resuelto/resuelta/finalizado/finalizada/no/false/0. Cualquier otro texto o ausencia queda desconocido y requiere revisión. La fecha final no decide el estado.

## Reto: detectar una modificación sin repetir avisos

1. Carga la demo y compara tras revisar fuente y columnas.
2. Selecciona A y B, prepara el borrador y verifica que no se registra nada como comunicado.
3. Solo para el ejercicio ficticio, confirma y registra la comunicación.
4. Compara el mismo fichero: A y B ya no son seleccionables sin cambios.
5. Carga la demo actualizada: A cambia, D aparece y B está ausente. B no está resuelta.
6. Añade una prueba que falle si borrar B de un fichero parcial la marca como resuelta.
7. Ampliación: define una política institucional de revisión de alertas desconocidas sin inferir disponibilidad ni decisiones clínicas. Prueba cada regla antes de adoptarla.

El adaptador de fuentes es la importación de ficheros, no una API oculta. Para integrar una API futura verifica documentación, licencia, esquemas, paginación y estado del servicio; conserva el modo manual y no envíes el catálogo hospitalario a terceros. No añadas claves al frontend.

No existe envío automático. Una ampliación de correo requeriría arquitectura, permisos y evaluación institucional separados.
