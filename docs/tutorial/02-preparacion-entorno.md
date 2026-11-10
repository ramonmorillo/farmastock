# 2. Preparación del entorno

Repositorio independiente: https://github.com/ramonmorillo/farmastock.

```sh
git clone https://github.com/ramonmorillo/farmastock.git
cd farmastock
git switch -c ejercicio/farmastock
npm run serve
```

Si la versión inicial no está incorporada a main, parte de feature/farmastock. Abre la raíz del servidor y tutorial.html. Usa HTTP local, no file://, para los módulos y documentos. Node 24 y Python 3 son suficientes; no hace falta npm install, API o compilación.

En la nube utiliza el checkout existente: cada tarea ya está aislada. No crees worktrees salvo petición explícita. Conserva cambios ajenos y comprueba git status.

## Claude Code y Codex

Claude Code: sigue https://code.claude.com/docs/ para tu instalación, entra en la carpeta con claude y pide inspección antes de modificar. Codex: sigue https://developers.openai.com/codex/ para terminal, editor o nube, selecciona el repositorio y verifica rama y permisos. En ambos casos aporta el prompt del paso 3 y pide ejecutar pruebas, sin enviar ficheros confidenciales ni incluir credenciales en frontend.

El agente puede requerir cuenta o plan propio, pero la aplicación no depende de un servicio de IA. Conserva assets y sus licencias si copias el proyecto. Las rutas relativas se prueban bajo /farmastock/.

Ejercicio: localiza core.mjs, files.mjs y app.mjs y distingue comparación, lectura de ficheros e interfaz.
