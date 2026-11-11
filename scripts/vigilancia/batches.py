"""Resume bounded public-data batches. Never loads recipients or sends mail."""
import argparse
import json
import pathlib
import subprocess
import sys

from preview import records, enrichments

BRANCH = 'probe/cima-access-v2'
ROOT = pathlib.Path(__file__).resolve().parents[2]


def coverage(report):
    wanted = {r['cn'] for r in records(report)}
    verified = wanted & set(enrichments(report))
    return {'total': len(wanted), 'verified': len(verified), 'pending': len(wanted-verified)}


def invoke(cache, budget):
    subprocess.run([sys.executable, str(ROOT/'scripts/vigilancia/probe.py'), '--cache', str(cache), '--budget-seconds', str(budget)], cwd=ROOT, check=True)
    return json.loads((ROOT/'reports/cima-probe.json').read_text())


def publish(report, directory, batch):
    """Only collector output enters the public data worktree; preserve history."""
    directory = pathlib.Path(directory)
    coverage(report)  # Validate source integrity before replacing the public snapshot.
    destination = directory/'reports/cima-probe.json'
    destination.parent.mkdir(exist_ok=True)
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(destination)
    git = ['git', '-C', str(directory)]
    subprocess.run(git+['add', '--', 'reports/cima-probe.json'], check=True)
    subprocess.run(git+['-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com', 'commit', '-m', f'Conserva lote CIMA {batch} con cobertura verificada'], check=True)
    subprocess.run(git+['push', 'origin', 'HEAD:refs/heads/'+BRANCH], check=True)


def run_batches(cache, directory, max_batches=6, budget=360, collect=invoke, persist=publish):
    if not 1 <= max_batches <= 8 or not 30 <= budget <= 1200:
        raise ValueError('Límites de lote inválidos.')
    outcomes = []
    stalled = 0
    before = None
    for batch in range(1, max_batches+1):
        report = collect(cache, budget)
        state = coverage(report)
        # Persist each successful source capture before starting another batch.
        persist(report, directory, batch)
        entry = dict(state, batch=batch, checked_at=report['checked_at'])
        outcomes.append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
        if state['pending'] == 0:
            return {'complete': True, 'reason': 'complete', 'batches': outcomes}
        limited = any(r.get('status') == 429 or r.get('error') == 'RateLimited' for r in report.get('medicines', []))
        if limited:
            return {'complete': False, 'reason': 'rate-limit-stop', 'batches': outcomes}
        stalled = stalled+1 if before is not None and state['pending'] >= before else 0
        if stalled >= 2:
            return {'complete': False, 'reason': 'no-progress-stop', 'batches': outcomes}
        before = state['pending']
        cache = pathlib.Path(directory)/'reports/cima-probe.json'
    return {'complete': False, 'reason': 'batch-limit', 'batches': outcomes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', required=True)
    parser.add_argument('--publish-dir', required=True)
    parser.add_argument('--max-batches', type=int, default=6)
    parser.add_argument('--budget-seconds', type=int, default=360)
    args = parser.parse_args()
    result = run_batches(pathlib.Path(args.cache), pathlib.Path(args.publish_dir), args.max_batches, args.budget_seconds)
    pathlib.Path('reports').mkdir(exist_ok=True)
    pathlib.Path('reports/batches-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print('Resultado por lotes:',result['reason'],flush=True)
    raise SystemExit(0 if result['complete'] else 2)
