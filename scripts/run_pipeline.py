"""Full optimization pipeline for py-unicode-golf.

Runs every stage in order and exports stats at the end.
The DB is always left in the depth-optimal Dijkstra state.

Stages (in order):
  1  minimal     — snapshot base-3 stats with only seeds 0 and 1
  2  populate    — seed DB with base-3 (44 anchors)
  3  iterative   — iterative DP optimizer (offset ≤ 2)
  4  deep        — iterative DP optimizer (offset ≤ 10)
  5  dijkstra    — Dijkstra depth + length (DB left in depth state)
  6  export      — write static/data/*.js

Usage:
    python scripts/run_pipeline.py              # run all stages
    python scripts/run_pipeline.py --from deep  # skip to stage 4+
    python scripts/run_pipeline.py --only export
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

STAGE_ORDER = ['minimal', 'populate', 'iterative', 'deep', 'dijkstra', 'export']


def run_minimal():
    from core.db import snapshot_minimal_formula
    print('\n── Stage 1: minimal formula snapshot ──')
    snapshot_minimal_formula()


def run_populate():
    from core.db import populate
    print('\n── Stage 2: populate (base-3, 44 anchors) ──')
    populate()


def run_iterative():
    from core.db import init_db, snapshot
    from core.strategies import apply_strategy
    from scripts.optimize_iterative import run_pass
    print('\n── Stage 3: iterative optimizer (offset ≤ 2) ──')
    init_db()
    n = run_pass()
    print(f'Improved {n} entries.')
    snapshot(f'iterative optimizer (offset \u2264 2)', improvements=n)


def run_deep():
    from core.db import init_db, snapshot
    from scripts.optimize_iterative import run_pass
    print('\n── Stage 4: deep search (offset ≤ 10) ──')
    init_db()
    n = run_pass(max_offset=10)
    print(f'Improved {n} entries.')
    snapshot(f'iterative optimizer (offset \u2264 10)', improvements=n)


def run_dijkstra():
    from scripts.optimize import run_dijkstra as _dijkstra, STRATEGIES as FWD, PathTracker, PAREN_LIMIT
    from core.strategies import apply_strategy
    from core.db import bulk_write, snapshot, init_db, MAX_N
    import scripts.optimize as opt

    init_db()

    for metric in ('depth', 'length'):
        print(f'\n── Stage 5: Dijkstra (metric={metric}) ──')
        opt.METRIC = metric
        t0 = datetime.now()
        nodes = _dijkstra()
        elapsed = (datetime.now() - t0).total_seconds()
        print(f'Done in {elapsed:.1f}s — {len(nodes):,} nodes.')
        written = bulk_write(nodes)
        print(f'Wrote {written:,} rows.')
        snapshot(f'dijkstra (metric={metric})', improvements=written)

    # Leave DB in depth-optimal state
    print('\n  Restoring depth-optimal state...')
    opt.METRIC = 'depth'
    nodes = _dijkstra()
    bulk_write(nodes)
    print('  Done.')


def run_export():
    from scripts.export_stats import export
    print('\n── Stage 6: export stats ──')
    export()


STAGES = {
    'minimal':   run_minimal,
    'populate':  run_populate,
    'iterative': run_iterative,
    'deep':      run_deep,
    'dijkstra':  run_dijkstra,
    'export':    run_export,
}


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--only' in args:
        stages = [args[args.index('--only') + 1]]
    elif '--from' in args:
        start = args[args.index('--from') + 1]
        idx = STAGE_ORDER.index(start)
        stages = STAGE_ORDER[idx:]
    else:
        stages = STAGE_ORDER

    t_total = datetime.now()
    for stage in stages:
        if stage not in STAGES:
            print(f'Unknown stage: {stage}. Choose from: {", ".join(STAGE_ORDER)}')
            sys.exit(1)
        STAGES[stage]()

    elapsed = (datetime.now() - t_total).total_seconds()
    print(f'\nPipeline complete in {elapsed:.1f}s.')
