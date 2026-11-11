"""Reviewable pilot drafts. No mail transport, credentials, or sending state."""
import argparse
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
from zoneinfo import ZoneInfo

SOURCE = 'https://cima.aemps.es/cima/publico/listadesabastecimiento.html'
RULES_PATH = pathlib.Path(__file__).with_name('rules.json')
REVIEW = 'resto-pendiente-de-clasificacion'


def records(report):
    pages = [r for r in report.get('requests', []) if
             re.fullmatch(r'https://cima\.aemps\.es/cima/rest/psuministro\?pagina=\d+', r.get('url', ''))]
    if not pages or not isinstance(pages[0].get('payload'), dict):
        raise ValueError('No hay una primera página válida de CIMA.')
    first = pages[0]['payload']
    total, size = first.get('totalFilas'), first.get('tamanioPagina')
    if type(total) is not int or type(size) is not int or not 0 <= total <= 10000 or not 0 < size <= 1000:
        raise ValueError('Paginación fuera de límites.')
    count = max(1, (total + size - 1) // size)
    if len(pages) != count:
        raise ValueError('Descarga incompleta: faltan páginas.')
    rows = []
    for expected, page in enumerate(pages, 1):
        data = page.get('payload', {})
        if page.get('status') != 200 or page.get('error') or data.get('pagina') != expected or data.get('totalFilas') != total or data.get('tamanioPagina') != size:
            raise ValueError('Páginas inconsistentes o consulta fallida.')
        batch = data.get('resultados')
        if not isinstance(batch, list) or len(batch) != min(size, total-len(rows)):
            raise ValueError('Página incompleta.')
        rows.extend(batch)
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('cn'), str) or not re.fullmatch(r'\d{6}', row['cn']) or type(row.get('activo')) is not bool or type(row.get('fini')) is not int or not isinstance(row.get('nombre'), str):
            raise ValueError('Registro inválido: no se omite silenciosamente.')
        date(row['fini'])
        if row.get('ffin') is not None:
            date(row['ffin'])
        if not isinstance(row.get('observ', ''), str):
            raise ValueError('Observaciones inválidas.')
        key = (row['cn'], row['fini'])
        if key in seen:
            raise ValueError('Incidencia duplicada: revisar captura.')
        seen.add(key)
    return rows


def signature(row):
    values = {k: row.get(k) for k in ['cn', 'nombre', 'fini', 'ffin', 'activo', 'observ', 'tipoProblemaSuministro']}
    return hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def changes(current, previous=None):
    old = {(r['cn'], r['fini']): r for r in previous or []}
    present = set()
    out = []
    for row in current:
        key = (row['cn'], row['fini'])
        present.add(key)
        before = old.get(key)
        if previous is None:
            kind = 'situacion-inicial'
        elif before is None:
            kind = 'nueva'
        elif before['activo'] and not row['activo']:
            kind = 'inactiva-en-fuente'
        elif not before['activo'] and row['activo']:
            kind = 'reactivada'
        else:
            kind = 'modificada' if signature(row) != signature(before) else 'sin-cambios'
        out.append(dict(row, change=kind))
    missing = [dict(row, change='ausente-revisar') for key, row in old.items() if key not in present]
    return out, missing


def load_rules(path=RULES_PATH):
    rules = json.loads(pathlib.Path(path).read_text())
    if rules.get('approved') is not False:
        raise ValueError('Este piloto solo admite reglas candidatas, no aprobadas.')
    areas = rules['areas']
    for area, rule in areas.items():
        if not re.fullmatch(r'[a-z-]+', area) or not isinstance(rule['label'], str):
            raise ValueError('Área inválida.')
        if any(not re.fullmatch(r'[A-Z][0-9]{2}[A-Z0-9]{0,4}', p) for p in rule['prefixes']):
            raise ValueError('Prefijo ATC inválido.')
    for cn, selected in rules.get('cn_overrides', {}).items():
        if not re.fullmatch(r'\d{6}', cn) or not selected or set(selected)-set(areas):
            raise ValueError('Excepción CN inválida.')
    return rules


def classify(row, medicine, rules):
    selected = {}
    explicit = rules.get('cn_overrides', {}).get(row['cn'])
    if explicit:
        return list(explicit), {a: ['Asignación explícita por CN, pendiente de aprobación'] for a in explicit}
    codes = {a.get('codigo', '') for a in (medicine or {}).get('atcs', []) if isinstance(a, dict)}
    codes = {code for code in codes if isinstance(code, str) and re.fullmatch(r'[A-Z][0-9]{2}[A-Z0-9]{0,4}', code)}
    # CIMA returns several levels: use the most specific codes, so parent groups
    # cannot undo a specific exception (e.g. lenalidomide and its L04 parent).
    leaves = sorted(c for c in codes if not any(other != c and other.startswith(c) for other in codes))
    for code in leaves:
        override = rules.get('exact_atc_overrides', {}).get(code)
        if override is not None:
            for area in override:
                selected.setdefault(area, []).append(f'Excepción ATC {code}; asignación candidata')
            continue
        for area, rule in rules['areas'].items():
            for prefix in rule['prefixes']:
                if code.startswith(prefix):
                    selected.setdefault(area, []).append(f'ATC {code}, regla {prefix}; asignación candidata')
                    break
    if not selected:
        reason = 'Sin metadatos verificados para este CN' if medicine is None else 'Sin regla candidata para el ATC disponible'
        selected[REVIEW] = [reason + '; revisión manual, sin especialidad inferida']
    return list(selected), selected


def date(value):
    if value is None:
        return 'No indicado'
    if type(value) is not int:
        raise ValueError('Fecha inválida.')
    dt = datetime.datetime.fromtimestamp(value/1000, datetime.timezone.utc).astimezone(ZoneInfo('Europe/Madrid'))
    if not 1900 <= dt.year <= 2200:
        raise ValueError('Fecha fuera de límites.')
    return dt.strftime('%d/%m/%Y')


def timestamp(value):
    dt = datetime.datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError('La captura necesita zona horaria.')
    return dt.astimezone(ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y %H:%M %Z')


def enrichments(report):
    enriched = {}
    for response in report.get('medicines', []):
        match = re.fullmatch(r'https://cima\.aemps\.es/cima/rest/medicamento\?cn=(\d{6})', response.get('url', ''))
        medicine = response.get('payload')
        if not match or response.get('status') != 200 or response.get('error') or not isinstance(medicine, dict):
            continue
        cn = match[1]
        if isinstance(medicine.get('atcs'), list) and any(str(p.get('cn')) == cn for p in medicine.get('presentaciones', []) if isinstance(p, dict)):
            enriched[cn] = medicine
    return enriched


def build(report, assignments, rules=None, previous=None):
    rules = rules or load_rules()
    rows = records(report)
    timestamp(report['checked_at'])
    previous_rows = records(previous) if previous is not None else None
    if previous is not None:
        timestamp(previous['checked_at'])
        if datetime.datetime.fromisoformat(previous['checked_at']) >= datetime.datetime.fromisoformat(report['checked_at']):
            raise ValueError('La captura anterior debe ser anterior a la actual.')
    enriched = enrichments(report)
    old_metadata = enrichments(previous) if previous is not None else {}
    metadata_dates = {}
    for snapshot in [previous, report]:
        if snapshot is None:
            continue
        for response in snapshot.get('medicines', []):
            cn=response.get('url','').split('cn=')[-1]
            if response.get('status')==200 and not response.get('error'):
                metadata_dates[cn]=response.get('fetched_at',snapshot['checked_at'])
    changed, missing = changes(rows, previous_rows)
    items = [r for r in changed if r['change'] != 'sin-cambios' and (previous is not None or r['activo'])] + missing
    all_areas = dict(rules['areas'], **{REVIEW: {'label': 'Pendientes de clasificación · revisión'}})
    area_items = {a: [] for a in all_areas}
    for row in items:
        metadata = old_metadata.get(row['cn']) if row['change'] == 'ausente-revisar' else enriched.get(row['cn'])
        areas, reasons = classify(row, metadata, rules)
        for area in areas:
            if metadata is not None and row['cn'] in metadata_dates:
                reasons[area].append('Metadatos consultados: '+timestamp(metadata_dates[row['cn']]))
            area_items[area].append(dict(row, reasons=reasons[area]))
    people = assignments.get('assignments', [])
    if assignments.get('mode') != 'preview-no-delivery' or not people:
        raise ValueError('Configuración privada inválida o modo distinto de prueba.')
    covered = set()
    owners = []
    for i, person in enumerate(people, 1):
        areas = person['areas']
        email = person['recipient']['email']
        if not re.fullmatch(r'[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+', email) or set(areas)-set(all_areas):
            raise ValueError('Destinatario o áreas inválidos.')
        covered.update(areas)
        grouped = {}
        for area in areas:
            for item in area_items[area]:
                key = (item['cn'], item['fini'])
                if key not in grouped:
                    grouped[key] = dict(item, areas=[], reasons=[])
                grouped[key]['areas'].append(all_areas[area]['label'])
                grouped[key]['reasons'].extend(item['reasons'])
        owner = {'id': f'responsable-{i}', 'recipient': person['recipient'], 'areas': [all_areas[a]['label'] for a in areas], 'items': list(grouped.values())}
        owner['subject'] = f'[PRUEBA SIN ENVÍO] FarmaStock · {len(grouped)} incidencias para revisión · {timestamp(report["checked_at"])}'
        owners.append(owner)
    if set(all_areas)-covered:
        raise ValueError('Hay áreas sin responsable; no se omiten silenciosamente.')
    return {
        'mode': 'preview-no-delivery', 'classification_approved': False,
        'rule_version': rules['version'], 'checked_at': report['checked_at'],
        'previous_at': previous.get('checked_at') if previous else None,
        'total': len(rows), 'active': sum(r['activo'] for r in rows),
        'unique_presentations': len({r['cn'] for r in rows}),
        'enriched_presentations': len({r['cn'] for r in rows} & set(enriched)),
        'unverified_presentations': len({r['cn'] for r in rows}-set(enriched)),
        'unchanged': sum(r['change']=='sin-cambios' for r in changed),
        'missing_for_review': len(missing),
        'area_counts': {all_areas[a]['label']: len(v) for a,v in area_items.items()},
        'rules_notes': rules['notes']+['Los metadatos ATC pueden reutilizarse hasta siete días si el CN y su nombre no cambian. Se conserva su fecha original en el motivo de asignación. El listado de suministro se descarga en cada ejecución.'], 'owners': owners,
    }


def render(result, owner):
    e = lambda value: html.escape(str(value), quote=True)
    notes = 'Primera captura: situación inicial de incidencias activas, no novedades desde ayer.' if result['previous_at'] is None else f'Cambios frente a {timestamp(result["previous_at"])}. Los casos sin cambios no se repiten.'
    rows = []
    for item in owner['items']:
        rows.append('<tr>' + ''.join(f'<td>{e(v)}</td>' for v in [
            item['cn'], item['nombre'], ', '.join(item['areas']), item['change'],
            ('Estado actual sin verificar; antes activo' if item['activo'] else 'Estado actual sin verificar; antes no activo') if item['change'] == 'ausente-revisar' else ('Activo' if item['activo'] else 'No activo declarado'), date(item['fini']), date(item.get('ffin')),
            '; '.join(item['reasons']), item.get('observ', 'No indicadas')]) + '</tr>')
    return '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FarmaStock · borrador de revisión</title><style>
body{font:1rem/1.5 system-ui;color:#152f44;background:#f4f7fa;margin:0}main{max-width:1400px;margin:auto;padding:24px}h1{color:#07505b}p,li{max-width:85ch}.notice{padding:16px;background:#fff1cd;border-left:5px solid #966800}.table{overflow:auto;background:white}table{border-collapse:collapse;width:100%;min-width:1100px}th,td{padding:12px;border-bottom:1px solid #d8e1e8;text-align:left;vertical-align:top}a{color:#07505b}summary{cursor:pointer}small{display:block}input{font:inherit;padding:10px;width:32rem;max-width:100%;box-sizing:border-box;margin:8px 0}caption{text-align:left;padding:12px;font-weight:600}@media(max-width:500px){main{padding:12px}}
</style><main><h1>FarmaStock Alert · revisión por responsable</h1><p class="notice"><strong>PRUEBA · NO ENVIADO.</strong> Reglas candidatas pendientes de revisión profesional. No constituye una comunicación oficial de AEMPS.</p>''' + \
        f'<h2>{e(owner["recipient"].get("name", "Tus áreas"))}</h2><p>{e(", ".join(owner["areas"]))}</p><p>Consulta: {e(timestamp(result["checked_at"]))}. {e(notes)}</p><p>Captura: {result["total"]} registros, {result["active"]} activos. CN con metadatos verificados: {result["enriched_presentations"]}/{result["unique_presentations"]}. Pendientes de verificación: {result["unverified_presentations"]}.</p><p>Este borrador contiene {len(owner["items"])} incidencias, deduplicadas entre tus áreas. Una tabla vacía no demuestra ausencia de problemas. La fecha de fin declarada no garantiza reposición; un registro ausente requiere revisión.</p><p><a href="{SOURCE}">Consultar la fuente oficial CIMA</a></p><details><summary>Reglas y límites de esta prueba</summary><ul>' + \
        ''.join(f'<li>{e(n)}</li>' for n in result['rules_notes']) + \
        f'</ul><p>Versión: {e(result["rule_version"])}. Pediatría sigue pendiente de asignaciones por presentación revisadas.</p></details><p><label for="search">Filtrar por medicamento, CN o área</label><br><input id="search" type="search" placeholder="Escribe para filtrar"><small id="visible" role="status" aria-live="polite"></small></p><div class="table" role="region" aria-label="Incidencias para revisión" tabindex="0"><table><caption>Incidencias candidatas; sin envío de correo</caption><thead><tr>' + \
        ''.join(f'<th scope="col">{v}</th>' for v in ['CN','Presentación','Áreas','Cambio','Estado de la fuente','Inicio','Fin declarado','Motivo de asignación','Observaciones oficiales']) + \
        '</tr></thead><tbody>' + ''.join(rows) + '''</tbody></table></div></main><script>
const search=document.getElementById('search');
const rows=[...document.querySelectorAll('tbody tr')];
function filter(){const q=search.value.trim().toLocaleLowerCase('es');let count=0;
for(const row of rows){row.hidden=!row.textContent.toLocaleLowerCase('es').includes(q);if(!row.hidden)count++;}
document.getElementById('visible').textContent=count+' de '+rows.length+' incidencias visibles';}
search.addEventListener('input',filter);filter();
</script></html>'''


def write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(text)
    os.chmod(path, 0o600)


def render_index(result):
    e = lambda value: html.escape(str(value), quote=True)
    links = ''.join(f'<li><a href="{o["id"]}.html">{e(o["recipient"].get("name", "Tus áreas"))}</a>: {len(o["items"])} incidencias para revisión. {e(", ".join(o["areas"]))}.</li>' for o in result['owners'])
    counts = ''.join(f'<tr><th scope="row">{e(area)}</th><td>{count}</td></tr>' for area,count in result['area_counts'].items())
    return f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FarmaStock · prueba por áreas</title><style>body{{font:1rem/1.6 system-ui;color:#152f44;background:#f4f7fa;margin:24px auto;padding:16px;max-width:900px}}a{{color:#07505b}}li{{margin:16px 0}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #ccd}}table{{width:100%;border-collapse:collapse}}.notice{{padding:16px;background:#fff1cd}}</style><h1>FarmaStock Alert · prueba por áreas</h1><p class="notice"><strong>Sin envío de correos. Reglas candidatas.</strong> Primera captura o comparación de prueba, sin vigilancia diaria activada. No es validación clínica.</p><p>Captura: {e(timestamp(result['checked_at']))}. Registros: {result['total']}; activos: {result['active']}. Metadatos verificados: {result['enriched_presentations']}/{result['unique_presentations']} CN.</p><h2>Resúmenes privados por responsable</h2><ul>{links}</ul><h2>Distribución candidata</h2><p>Una incidencia puede corresponder a varias áreas. Pediatría requiere asignaciones explícitas revisadas. El resto es una bandeja de revisión, sin especialidad inferida.</p><table><caption>Incidencias incluidas en esta prueba</caption><thead><tr><th scope="col">Área</th><th scope="col">Incidencias</th></tr></thead><tbody>{counts}</tbody></table><p><a href="{SOURCE}">Fuente oficial CIMA</a></p></html>'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('--assignments', required=True)
    parser.add_argument('--previous')
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    folder = pathlib.Path(args.out_dir).resolve()
    repo = pathlib.Path(__file__).resolve().parents[2]
    if folder.is_relative_to(repo) or not folder.is_dir() or folder.stat().st_mode & 0o077:
        raise SystemExit('Elige un directorio privado (700) fuera del repositorio.')
    load = lambda path: json.loads(pathlib.Path(path).read_text())
    result = build(load(args.report), load(args.assignments), previous=load(args.previous) if args.previous else None)
    write_private(folder/'drafts.json', json.dumps(result, ensure_ascii=False, indent=2))
    for owner in result['owners']:
        write_private(folder/(owner['id']+'.html'), render(result, owner))
    write_private(folder/'index.html', render_index(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ['owners','rules_notes']}, ensure_ascii=False))
    print(f'{len(result["owners"])} borradores privados generados. Envíos: 0.')
