"""
Dijkstra-based optimizer for py-unicode-golf.

Runs a forward-search shortest-path algorithm over the integer graph 
from 0 to MAX_N. Priority queue ensures absolute shortest paths.
"""

import sys
import os
import heapq
from datetime import datetime

# Setup path to import from core module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.anchors import BASE_ANCHORS
from core.db import get_conn, apply_strategy, snapshot, stats, init_db, MAX_N

# ── Configuration ─────────────────────────────────────────────────────────────

METRIC = 'depth'        # Sort queue by 'depth' (parens) or 'length' (chars)
PAREN_LIMIT = 200       # Python's hard limit for nested AST nodes


# ── Strategies ────────────────────────────────────────────────────────────────

def build_forward_strategies():
    """Defines the forward mathematical operations for every single-step edge."""
    strategies_list = [
        ('decrement',      lambda number: number - 1),
        ('triple',         lambda number: 3 * number),
        ('quad_plus_3',    lambda number: 4 * number + 3),
        ('quint_plus_5',   lambda number: 5 * number + 5),
        ('triangular',     lambda number: number * (number - 1) // 2),
        ('enum_list_8x',   lambda number: 8 * number if 1 <= number <= 10 else -1),
        ('slice_offset',   lambda number: len(str(number)) + 19 if number > 0 else -1),
        ('complex_offset', lambda number: len(str(number)) + 5 if number > 0 else -1),
    ]
    
    for k in range(1, 6):
        strategies_list.append((f'zip_chain_{k}', lambda number, multiplier=3*(k+1): multiplier * number))
        
    for k in range(1, 12):
        strategies_list.append((f'ascii_exp_{k}', lambda number, multiplier=(1<<k)+3, constant=(1<<(k+1))+1: multiplier * number + constant))
        
    return strategies_list

STRATEGIES = build_forward_strategies()


# ── State Management ──────────────────────────────────────────────────────────

class PathTracker:
    def __init__(self, metric='depth'):
        self.metric = metric
        self.priority_queue = []
        self.best_primary_cost = {}
        self.best_secondary_cost = {}
        self.graph_nodes = {}

    def add_path(self, target_number, expression_string, strategy_name='base', parent_number=None, decrement_count=0):
        depth_cost = expression_string.count('(')
        length_cost = len(expression_string)
        
        primary_cost = depth_cost if self.metric == 'depth' else length_cost
        secondary_cost = length_cost if self.metric == 'depth' else depth_cost
        
        current_best_primary = self.best_primary_cost.get(target_number, float('inf'))
        current_best_secondary = self.best_secondary_cost.get(target_number, float('inf'))
        
        # If strictly cheaper, or tied on primary but cheaper on secondary
        if primary_cost < current_best_primary or (primary_cost == current_best_primary and secondary_cost < current_best_secondary):
            self.best_primary_cost[target_number] = primary_cost
            self.best_secondary_cost[target_number] = secondary_cost
            
            self.graph_nodes[target_number] = {
                'expr': expression_string, 
                'depth': depth_cost, 
                'len': length_cost, 
                'strategy': strategy_name, 
                'parent': parent_number, 
                'offset': decrement_count
            }
            heapq.heappush(self.priority_queue, (primary_cost, secondary_cost, target_number))

    def pop_best_unexplored_node(self):
        while self.priority_queue:
            primary_cost, secondary_cost, target_number = heapq.heappop(self.priority_queue)
            
            # Ensure this queued path hasn't been beaten by a better path found later
            if primary_cost <= self.best_primary_cost.get(target_number, float('inf')) and \
               secondary_cost <= self.best_secondary_cost.get(target_number, float('inf')):
                
                return target_number, self.graph_nodes[target_number]['expr'], self.graph_nodes[target_number]['depth']
                
        return None, None, None


# ── Algorithm Loop ────────────────────────────────────────────────────────────

def run_dijkstra():
    tracker = PathTracker(metric=METRIC)
    
    # Seed the queue with starting anchors
    for anchor_value, anchor_expression in BASE_ANCHORS.items():
        tracker.add_path(target_number=anchor_value, expression_string=anchor_expression)

    while True:
        source_number, source_expression, source_depth = tracker.pop_best_unexplored_node()
        
        if source_number is None: 
            break

        for strategy_name, forward_math_function in STRATEGIES:
            target_number = forward_math_function(source_number)
            
            # Bound check
            if not (0 <= target_number <= MAX_N):
                continue
            
            # Lower-bound pruning: Every strategy (including decrement) adds at least 2 parens.
            predicted_min_depth = source_depth + 2
            if predicted_min_depth >= tracker.best_primary_cost.get(target_number, float('inf')):
                continue

            try:
                # Apply the specific string transformation for the strategy
                if strategy_name == 'decrement':
                    # Fallback to manual string construction if apply_strategy doesn't support 'decrement' internally yet
                    target_expression = f'max(range({source_expression}))'
                    decrement_count = 1
                else:
                    target_expression = apply_strategy(strategy_name, source_expression, offset=0)
                    decrement_count = 0
                
                if target_expression.count('(') >= PAREN_LIMIT:
                    continue
                    
                tracker.add_path(
                    target_number=target_number, 
                    expression_string=target_expression, 
                    strategy_name=strategy_name, 
                    parent_number=source_number, 
                    decrement_count=decrement_count
                )
            except ValueError:
                pass
                    
    return tracker.graph_nodes


# ── Database Operations ───────────────────────────────────────────────────────

def bulk_write(nodes_dictionary):
    rows = [
        (number, data['expr'], data['depth'], data['len'], data['strategy'], data['parent'], data['offset']) 
        for number, data in nodes_dictionary.items()
    ]
    conn = get_conn()
    conn.execute('DELETE FROM numbers')
    conn.executemany('INSERT INTO numbers VALUES (?,?,?,?,?,?,?)', rows)
    conn.commit()


# ── Execution ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    
    print(f"Running flattened Dijkstra graph search (metric={METRIC})...")
    start_time = datetime.now()
    
    final_graph = run_dijkstra()
    
    elapsed_time = (datetime.now() - start_time).total_seconds()
    print(f"Search completed in {elapsed_time:.1f}s. Found paths for {len(final_graph):,} numbers.")
    
    print("Writing graph to database...")
    bulk_write(final_graph)
    
    snapshot(f'dijkstra ({METRIC})', improvements=len(final_graph))
    stats()