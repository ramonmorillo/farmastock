"""Public-data-only daily pilot. No recipient config or mail capability."""
import argparse
import datetime
import json
import pathlib
from zoneinfo import ZoneInfo

from batches import run_batches


def should_collect(snapshot, now=None, force=False):
    now=now or datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is None:raise ValueError('La hora actual necesita zona horaria.')
    previous=datetime.datetime.fromisoformat(snapshot['checked_at'])
    if previous.tzinfo is None:raise ValueError('La captura necesita zona horaria.')
    if previous>now:raise ValueError('La captura está fechada en el futuro.')
    if force:return True
    local=now.astimezone(ZoneInfo('Europe/Madrid'))
    return local.hour>=8 and previous.astimezone(ZoneInfo('Europe/Madrid')).date()<local.date()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache',required=True);parser.add_argument('--publish-dir',required=True)
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args();cache=pathlib.Path(args.cache)
    if not should_collect(json.loads(cache.read_text()),force=args.force):
        print('Captura diaria omitida: ya existe una de hoy o aún no son las 08:00 en Europe/Madrid.')
        raise SystemExit(0)
    result=run_batches(cache,pathlib.Path(args.publish_dir),max_batches=1)
    print('Captura diaria de prueba, sin correos:',result['reason'])
    raise SystemExit(0 if result['complete'] else 2)
