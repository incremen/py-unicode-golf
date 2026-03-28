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
from core.strategies import apply_strategy


METRIC      = 'depth'   # 'depth' or 'length'
PAREN_LIMIT = 200



def build_forward_strategies():
    strategies_list = [
        ('decrement',      lambda source_number: source_number - 1),
        ('triple',         lambda source_number: 3 * source_number),
        ('quad_plus_3',    lambda source_number: 4 * source_number + 3),
        ('quint_plus_5',   lambda source_number: 5 * source_number + 5),
        ('triangular',     lambda source_number: source_number * (source_number - 1) // 2),
        ('enum_list_8x',   lambda source_number: 8 * source_number if 1 <= source_number <= 10 else -1),
        ('slice_offset',   lambda source_number: len(str(source_number)) + 19 if source_number > 0 else -1),
        ('complex_offset', lambda source_number: len(str(source_number)) + 5  if source_number > 0 else -1),
    ]
    
    for zip_count in range(1, 6):
        strategies_list.append((
            f'zip_chain_{zip_count}', 
            lambda source_number, multiplier=3*(zip_count+1): multiplier * source_number
        ))
        
    for ascii_count in range(1, 12):
        strategies_list.append((
            f'ascii_exp_{ascii_count}', 
            lambda source_number, multiplier=(1<<ascii_count)+3, constant_addition=(1<<(ascii_count+1))+1: multiplier * source_number + constant_addition
        ))
        
    return strategies_list

STRATEGIES = build_forward_strategies()



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

        for strategy_name, forward_function in STRATEGIES:
            target_number = forward_function(source_number)

            if not (0 <= target_number <= MAX_N):
                continue

            target_best_primary, target_best_secondary = weights.get(target_number, (float('inf'), float('inf')))
            
            # Lower-bound depth pruning: every strategy adds ≥ 2 parens
            if source_depth + 2 >= target_best_primary:
                continue

            try:
                # Evaluate the edge
                target_expression = apply_strategy(strategy_name, source_expression, offset=0)
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

    init_db()
    print(f'Running Dijkstra graph search (metric={METRIC})...')
    
    start_time = datetime.now()
    final_graph = run_dijkstra()
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    print(f'Search completed in {elapsed_time:.1f}s. Found paths for {len(final_graph):,} numbers.')

    print('Writing graph to database...')
    rows_inserted = bulk_write(final_graph)
    print(f'Inserted {rows_inserted:,} rows.')

    snapshot(f'dijkstra (metric={METRIC})', improvements=rows_inserted)
    stats()