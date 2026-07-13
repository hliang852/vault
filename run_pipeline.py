#!/usr/bin/env python3
"""
run_pipeline.py -- one-command orchestrator for the integrated project.

Chain (Part 1 -> Part 2 -> Part 3):

  [--transform]  japan-ma/pipeline/transform.py   Japan_Master.csv -> Japan.csv
  1. src/explore.py                               data-quality report + figures
  2. src/cluster/precedent_engine.py              similarity graph + clusters
  3. viewer/build.py                              the interactive site

Usage:
  python run_pipeline.py                # explore -> engine -> site (Japan.csv as-is)
  python run_pipeline.py --transform    # regenerate Japan.csv from the master first
  python run_pipeline.py --watch        # poll japan-ma/data/Japan.csv; on any change,
                                        # auto-run explore -> engine -> site
  python run_pipeline.py --watch --interval 30

Each step runs only if the previous one succeeded; the pipeline stops loudly on
the first failure (never builds the site from stale/partial upstream output).
"""
import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
CANONICAL_CSV = REPO / 'japan-ma' / 'data' / 'Japan.csv'

STEPS = [
    ('Part 1 · explore', [sys.executable, str(REPO / 'src' / 'explore.py')]),
    ('Part 2 · precedent engine', [sys.executable, str(REPO / 'src' / 'cluster' / 'precedent_engine.py')]),
    ('Part 3 · site build', [sys.executable, str(REPO / 'viewer' / 'build.py')]),
]

TRANSFORM = ('Part 1 · transform', [
    sys.executable, str(REPO / 'japan-ma' / 'pipeline' / 'transform.py'),
    '--master', str(REPO / 'japan-ma' / 'data' / 'Japan_Master.csv'),
    '--outdir', str(REPO / 'japan-ma' / 'data'),
])


def run_step(name, cmd):
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run(cmd, cwd=REPO)
    if r.returncode != 0:
        print(f"\nPIPELINE STOPPED: '{name}' failed (exit {r.returncode}). "
              f"Downstream steps were NOT run.", file=sys.stderr)
        return False
    return True


def run_chain(transform_first=False):
    if not CANONICAL_CSV.exists():
        print(f"PIPELINE STOPPED: {CANONICAL_CSV} not found.", file=sys.stderr)
        return False
    steps = ([TRANSFORM] if transform_first else []) + STEPS
    for name, cmd in steps:
        if not run_step(name, cmd):
            return False
    print("\n=== pipeline complete: site is up to date with japan-ma/data/Japan.csv ===")
    return True


def csv_hash():
    try:
        return hashlib.sha256(CANONICAL_CSV.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def watch(interval):
    print(f"watching {CANONICAL_CSV} (every {interval}s) -- Ctrl-C to stop", flush=True)
    last = csv_hash()
    if last is None:
        print("note: file does not exist yet; will fire when it appears")
    while True:
        time.sleep(interval)
        cur = csv_hash()
        if cur is not None and cur != last:
            print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} -- Japan.csv changed, running pipeline", flush=True)
            ok = run_chain()
            print("watching again..." if ok else "fix the error above; watching again...", flush=True)
        last = cur if cur is not None else last


def main():
    ap = argparse.ArgumentParser(description='Run the Part 1 -> 2 -> 3 pipeline')
    ap.add_argument('--transform', action='store_true',
                    help='regenerate Japan.csv from Japan_Master.csv first')
    ap.add_argument('--watch', action='store_true',
                    help='poll Japan.csv and auto-run the chain on any change')
    ap.add_argument('--interval', type=int, default=15, help='watch poll seconds (default 15)')
    args = ap.parse_args()
    if args.watch:
        if args.transform:
            print('--transform is ignored in --watch mode (the watcher reacts to '
                  'Japan.csv changes; run the transform separately or via Part 1).')
        try:
            watch(args.interval)
        except KeyboardInterrupt:
            print('\nstopped.')
        return 0
    return 0 if run_chain(transform_first=args.transform) else 1


if __name__ == '__main__':
    sys.exit(main())
