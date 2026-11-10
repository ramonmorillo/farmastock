const docs = new Map();
async function readDoc(name) {
  if (!/^[a-z0-9-]+\.md$/.test(name)) throw new Error('Documento no válido.');
  if (!docs.has(name)) docs.set(name, fetch(new URL(`./docs/tutorial/${name}`, import.meta.url)).then(response => { if (!response.ok) throw new Error('Documento no disponible.'); return response.text(); }).catch(error => { docs.delete(name); throw error; }));
  return docs.get(name);
}
// Subconjunto Markdown deliberado: texto, títulos, listas y bloques de código.
// No se interpreta HTML ni se inserta contenido de documentos con innerHTML.
function markdown(text) {
  const fragment = document.createDocumentFragment(); let code = null;
  for (const line of text.split('\n')) {
    if (line.startsWith('```')) { if (code) code = null; else { code = document.createElement('pre'); fragment.append(code); } continue; }
    if (code) { code.textContent += line + '\n'; continue; }
    if (!line.trim()) continue;
    const heading = line.match(/^(#{1,6})\s+(.*)/);
    const node = document.createElement(heading ? `h${Math.min(6, heading[1].length + 2)}` : 'p');
    node.textContent = heading ? heading[2] : line;
    fragment.append(node);
  }
  return fragment;
}
for (const container of document.querySelectorAll('[data-doc]')) {
  const details = container.closest('details');
  details.addEventListener('toggle', async () => {
    if (!details.open || container.dataset.loaded) return;
    container.textContent = 'Cargando documento…';
    try { container.replaceChildren(markdown(await readDoc(container.dataset.doc))); container.dataset.loaded = 'true'; }
    catch { container.textContent = 'No se pudo cargar el documento. Usa el enlace Markdown de este apartado o inténtalo de nuevo.'; }
  });
}
for (const button of document.querySelectorAll('[data-copy-doc]')) button.addEventListener('click', async () => {
  const status = document.getElementById('tutorial-status');
  try { await navigator.clipboard.writeText(await readDoc(button.dataset.copyDoc)); status.textContent = 'Documento copiado. Revísalo y adáptalo antes de enviarlo a un agente.'; }
  catch { status.textContent = 'No se pudo copiar. Abre el documento Markdown y selecciona su texto manualmente.'; }
  status.scrollIntoView({ block: 'nearest' });
});
const checks = [...document.querySelectorAll('[data-progress]')], key = 'farmastock.tutorial.v1';
function update(save = false) {
  document.getElementById('tutorial-progress').textContent = `${checks.filter(c => c.checked).length} de 6 pasos revisados. Estas marcas no acreditan competencia ni validación clínica.`;
  if (save) try { sessionStorage.setItem(key, JSON.stringify(checks.filter(c => c.checked).map(c => c.dataset.progress))); } catch { /* La guía funciona también sin almacenamiento. */ }
}
try { const saved = JSON.parse(sessionStorage.getItem(key) || '[]'); if (Array.isArray(saved)) checks.forEach(c => { c.checked = saved.includes(c.dataset.progress); }); } catch { /* No se bloquea la lectura por datos dañados. */ }
checks.forEach(c => c.addEventListener('change', () => update(true)));
document.getElementById('tutorial-reset').addEventListener('click', () => { checks.forEach(c => { c.checked = false; }); update(true); });
update();
