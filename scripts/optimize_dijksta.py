"""Dijkstra optimizer for py-unicode-golf.

Builds the entire 0..MAX_N graph from BASE_ANCHORS and bulk-writes to SQLite.
Does not require a pre-populated DB — runs standalone.

CLI:
    python scripts/optimize.py                    — optimize for depth (default)
    python scripts/optimize.py --metric length    — optimize for expression length
"""

import sys
import os
import heapq
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.anchors import BASE_ANCHORS
from core.db import init_db, snapshot, stats, bulk_write, MAX_N
from core.strategies import apply_strategy, STRATEGIES

METRIC      = 'depth'   # 'depth' or 'length'
PAREN_LIMIT = 200



def run_dijkstra():
    priority_queue = []
    
    # target_number -> (primary_cost, secondary_cost)
    weights = {}
    
    # target_number -> {expr, depth, len, strategy, parent, offset}
    best_incoming_edges = {}

    # 1. Seed the queue with starting anchors
    for anchor_value, anchor_expression in BASE_ANCHORS.items():
        depth_cost = anchor_expression.count('(')
        length_cost = len(anchor_expression)
        
        primary_cost, secondary_cost = (depth_cost, length_cost) if METRIC == 'depth' else (length_cost, depth_cost)
        
        weights[anchor_value] = (primary_cost, secondary_cost)
        best_incoming_edges[anchor_value] = {
            'expr': anchor_expression, 'depth': depth_cost, 'len': length_cost,
            'strategy': 'base', 'parent': None,
        }
        heapq.heappush(priority_queue, (primary_cost, secondary_cost, anchor_value))

    # 2. Process the expanding graph
    while priority_queue:
        current_primary_cost, current_secondary_cost, source_number = heapq.heappop(priority_queue)

        # Skip stale nodes
        best_known_primary, best_known_secondary = weights.get(source_number, (float('inf'), float('inf')))
        if current_primary_cost > best_known_primary or (current_primary_cost == best_known_primary and current_secondary_cost > best_known_secondary):
            continue

        source_node = best_incoming_edges[source_number]
        source_expression = source_node['expr']
        source_depth = source_node['depth']

        for strategy_name, (forward_function, _) in STRATEGIES.items():
            target_number = forward_function(source_number)

            if not (0 <= target_number <= MAX_N):
                continue

            target_best_primary, target_best_secondary = weights.get(target_number, (float('inf'), float('inf')))
            
            # Lower-bound depth pruning: every strategy adds ≥ 2 parens
            if source_depth + 2 >= target_best_primary:
                continue

            try:
                # Evaluate the edge
                target_expression = apply_strategy(strategy_name, source_expression)
                target_depth = target_expression.count('(')
                
                if target_depth >= PAREN_LIMIT:
                    continue
                    
                target_length = len(target_expression)
                
                candidate_primary_cost, candidate_secondary_cost = (target_depth, target_length) if METRIC == 'depth' else (target_length, target_depth)

                # Relax the edge
                if candidate_primary_cost < target_best_primary or (candidate_primary_cost == target_best_primary and candidate_secondary_cost < target_best_secondary):
                    weights[target_number] = (candidate_primary_cost, candidate_secondary_cost)
                    
                    best_incoming_edges[target_number] = {
                        'expr': target_expression, 'depth': target_depth, 'len': target_length,
                        'strategy': strategy_name, 'parent': source_number,
                    }
                    heapq.heappush(priority_queue, (candidate_primary_cost, candidate_secondary_cost, target_number))

            except ValueError:
                pass

    return best_incoming_edges



if __name__ == '__main__':
    if '--metric' in sys.argv:
        METRIC = sys.argv[sys.argv.index('--metric') + 1]
    assert METRIC in ('depth', 'length'), f'Unknown metric: {METRIC}'

    from core.db import get_conn, generate_json
    init_db()

    conn = get_conn()
    baseline = {r[0]: r[1] for r in conn.execute('SELECT n, depth FROM numbers').fetchall()}
    conn.close()

    print('Running Dijkstra (metric=depth)...')
    t0 = datetime.now()
    METRIC = 'depth'
    depth_graph = run_dijkstra()
    print(f'  done in {(datetime.now()-t0).total_seconds():.1f}s')

    print('Running Dijkstra (metric=length)...')
    t0 = datetime.now()
    METRIC = 'length'
    length_graph = run_dijkstra()
    print(f'  done in {(datetime.now()-t0).total_seconds():.1f}s')

    print('Writing to database...')
    bulk_write(depth_graph, length_graph)
    generate_json()

    improved  = [(n, baseline[n], depth_graph[n]['depth']) for n in depth_graph if n in baseline and depth_graph[n]['depth'] < baseline[n]]
    regressed = [(n, baseline[n], depth_graph[n]['depth']) for n in depth_graph if n in baseline and depth_graph[n]['depth'] > baseline[n]]

    print(f'\nImprovements: {len(improved):,}  Regressions: {len(regressed):,}')

    if improved:
        improved.sort(key=lambda x: x[1] - x[2], reverse=True)
        print('Top improvements:')
        for n, old, new in improved[:10]:
            print(f'  n={n:>7}  depth {old} → {new}  (-{old - new})')

    if regressed:
        regressed.sort(key=lambda x: x[2] - x[1], reverse=True)
        print('Regressions:')
        for n, old, new in regressed[:10]:
            print(f'  n={n:>7}  depth {old} → {new}  (+{new - old})')

    snapshot('dijkstra (depth+length)', improvements=len(improved))

    with get_conn() as conn:
        rows = conn.execute(
            'SELECT label, avg_depth, max_depth, avg_len FROM optimization_log ORDER BY id DESC LIMIT 3'
        ).fetchall()
    print('\nLast 3 snapshots:')
    for label, avg_depth, max_depth, avg_len in reversed(rows):
        print(f'  {label}: avg_depth={avg_depth}  max_depth={max_depth}  avg_len={avg_len}')