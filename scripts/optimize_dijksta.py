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
    print("started dijkstra")
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

    from core.db import get_conn, merge_best, generate_json
    init_db()

    def run_and_merge(metric):
        global METRIC
        METRIC = metric
        print(f'Running Dijkstra (metric={metric})...')
        t0 = datetime.now()
        graph = run_dijkstra()
        print(f'  done in {(datetime.now()-t0).total_seconds():.1f}s — merging...')
        improved, regressed = merge_best(graph, metric)
        improved.sort(key=lambda x: (x[1] or 0) - x[2], reverse=True)
        print(f'  improvements: {len(improved):,}  regressions: {len(regressed):,}')
        if improved[:5]:
            for n, old, new in improved[:5]:
                print(f'    n={n:>7}  {metric} {old} → {new}')
        return len(improved)

    total = run_and_merge('depth') + run_and_merge('length')
    if total == 0:
        print('No improvements found — skipping DB write and snapshot.')
    else:
        generate_json()
        snapshot('dijkstra (depth+length)', improvements=total)

    with get_conn() as conn:
        how_many_snapshots = 6
        rows = conn.execute(
            f'SELECT label, avg_depth, max_depth, avg_len FROM optimization_log ORDER BY id DESC LIMIT {how_many_snapshots}'
        ).fetchall()
    print(f'\nLast {how_many_snapshots} snapshots:')
    for label, avg_depth, max_depth, avg_len in reversed(rows):
        print(f'  {label}: avg_depth={avg_depth}  max_depth={max_depth}  avg_len={avg_len}')