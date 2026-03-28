"""Test new Dijkstra strategies without writing to the database.

Add candidate strategies to NEW_STRATEGIES below, then run.

CLI:
    python scripts/test_strategy.py
"""

import sys, os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.strategies import STRATEGIES
from core.db import merge_best
import scripts.optimize_dijksta as opt


# ┌─────────────────────────────────────────────────────────┐
# │  ADD YOUR STRATEGIES HERE                               │
# │                                                         │
# │  'name': (lambda source_number: <math>,                 │
# │           lambda parent_expression: f'<expr>')          │
# └─────────────────────────────────────────────────────────┘

# ── Precomputed Lookup Tables (Takes ~1-2 seconds at startup) ──
print("Precomputing sequence lengths for strategies...")
start_time = time.time()
MAX_TEST_N = 200_000

DIGIT_SUM       = [0] * (MAX_TEST_N + 1)
LIST_RANGE_LEN  = [0] * (MAX_TEST_N + 1)
TUPLE_RANGE_LEN = [0] * (MAX_TEST_N + 1)
ZIP_RANGE_LEN   = [0] * (MAX_TEST_N + 1)
DICT_ENUM_RANGE = [0] * (MAX_TEST_N + 1)

LIST_RANGE_LEN[0] = TUPLE_RANGE_LEN[0] = ZIP_RANGE_LEN[0] = DICT_ENUM_RANGE[0] = 2
TUPLE_RANGE_LEN[1] = 4  # "(0,)" — single-element tuple has trailing comma

# Closed-form formulas (all O(1) per step once DIGIT_SUM is known):
#   list  [0,..,n-1]          = 2 + DIGIT_SUM[n] + 2*(n-1)
#   tuple (0,..,n-1) n>=2     = same as list
#   zip   [(0,),..(n-1,)]     = DIGIT_SUM[n] + 5*n
#   dict  {0:0,..,n-1:n-1}    = 2*DIGIT_SUM[n] + 4*n
for n in range(1, MAX_TEST_N + 1):
    DIGIT_SUM[n]        = DIGIT_SUM[n - 1] + len(str(n - 1))
    LIST_RANGE_LEN[n]   = 2 + DIGIT_SUM[n] + 2 * (n - 1)
    if n >= 2:
        TUPLE_RANGE_LEN[n] = 2 + DIGIT_SUM[n] + 2 * (n - 1)
    ZIP_RANGE_LEN[n]    = DIGIT_SUM[n] + 5 * n
    DICT_ENUM_RANGE[n]  = 2 * DIGIT_SUM[n] + 4 * n

print(f"Precomputation finished in {time.time() - start_time:.2f}s.\n")

NEW_STRATEGIES = {
    # ── Cheaper 4x Multiplier (3 parens instead of 4) ──
    # Exact math: 4 * source_number + 14
    # Why: str(bytearray(n)) evaluates to "bytearray(b'\x00...')"
    'bytearray_4x':   (lambda source_number: 4 * source_number + 14,
                       lambda parent_expression: f'len(str(bytearray({parent_expression})))'),

    # ── Base Conversions (2 parens) ──
    # Exact math: floor(log2(source_number)) + 3
    # Why: bin(10) -> '0b1010' (length 6). Extremely cheap logarithmic growth.
    'bin_len':        (lambda source_number: source_number.bit_length() + 2 if source_number > 0 else 3,
                       lambda parent_expression: f'len(bin({parent_expression}))'),

    # Exact math: floor(log16(source_number)) + 3
    'hex_len':        (lambda source_number: len(hex(source_number)),
                       lambda parent_expression: f'len(hex({parent_expression}))'),

    # Exact math: floor(log8(source_number)) + 3
    'oct_len':        (lambda source_number: len(oct(source_number)),
                       lambda parent_expression: f'len(oct({parent_expression}))'),

    # ── Cheap String Representation (2 parens) ──
    # Exact math: floor(log10(source_number)) + 10
    # Why: ascii(range(n)) -> "range(0, n)". Very cheap length bump for low parens.
    'ascii_range':    (lambda source_number: len(str(source_number)) + 10,
                       lambda parent_expression: f'len(ascii(range({parent_expression})))'),

    # ── Precomputed Table Lookups (4-5 parens) ──
    # Exact math: ~ source_number * log10(source_number)
    # Why: Stringifying a list of numbers grows as the numbers themselves gain digits.
    'list_range':     (lambda source_number: LIST_RANGE_LEN[source_number] if source_number <= MAX_TEST_N else -1,
                       lambda parent_expression: f'len(str(list(range({parent_expression}))))'),

    # Exact math: ~ source_number * log10(source_number)
    # Similar growth to list_range, but tuple formatting yields slightly different constants.
    'tuple_range':    (lambda source_number: TUPLE_RANGE_LEN[source_number] if source_number <= MAX_TEST_N else -1,
                       lambda parent_expression: f'len(str(tuple(range({parent_expression}))))'),

    # Exact math: ~ source_number * log10(source_number) + constant padding
    # Why: zip(range(3)) -> "[(0,), (1,), (2,)]"
    'zip_range':      (lambda source_number: ZIP_RANGE_LEN[source_number] if source_number <= MAX_TEST_N else -1,
                       lambda parent_expression: f'len(str(list(zip(range({parent_expression})))))'),

    # Exact math: ~ 2 * source_number * log10(source_number)
    # Why: dict(enumerate(range(2))) -> "{0: 0, 1: 1}"
    'dict_enum_range':(lambda source_number: DICT_ENUM_RANGE[source_number] if 0 <= source_number <= MAX_TEST_N else -1,
                       lambda parent_expression: f'len(str(dict(enumerate(range({parent_expression})))))'),

    # Exact math: ~ source_number * log10(source_number) + constant zeros
    # Why: enumerate(bytes(2)) -> "[(0, 0), (1, 0)]". The index grows, but the byte value is always 0.
    'list_enum_bytes':(lambda source_number: DIGIT_SUM[source_number] + (6 * source_number) + 2 if source_number > 0 else 2,
                       lambda parent_expression: f'len(str(list(enumerate(bytes({parent_expression})))))'),

    # Exact math: ~ source_number * log10(source_number) + constant zeros
    'dict_enum_bytes':(lambda source_number: DIGIT_SUM[source_number] + (5 * source_number) + 2 if source_number > 0 else 2,
                       lambda parent_expression: f'len(str(dict(enumerate(bytes({parent_expression})))))'),
}

# ┌─────────────────────────────────────────────────────────┐
# │  DON'T EDIT BELOW                                       │
# └─────────────────────────────────────────────────────────┘

if not NEW_STRATEGIES:
    print('No strategies defined. Add entries to NEW_STRATEGIES and re-run.')
    sys.exit(0)

from core.db import get_conn
conn = get_conn()
prev_avg_depth, prev_avg_len = conn.execute('SELECT AVG(depth), AVG(len) FROM numbers').fetchone()
conn.close()
print(f'current db:  avg_depth={prev_avg_depth:.4f}  avg_len={prev_avg_len:.4f}\n')

STRATEGIES.update(NEW_STRATEGIES)

for test_metric in ('depth', 'length'):
    opt.METRIC = test_metric
    optimized_graph = opt.run_dijkstra()

    avg_depth = sum(n['depth'] for n in optimized_graph.values()) / len(optimized_graph)
    avg_len   = sum(n['len']   for n in optimized_graph.values()) / len(optimized_graph)

    improved_nodes, regressed_nodes = merge_best(optimized_graph, test_metric, write=False)
    improved_nodes.sort(key=lambda item: (item[1] or 0) - item[2], reverse=True)

    d_delta = avg_depth - prev_avg_depth
    l_delta = avg_len   - prev_avg_len
    print(f'metric={test_metric}:')
    print(f'  avg_depth {prev_avg_depth:.4f} → {avg_depth:.4f}  ({d_delta:+.4f})')
    print(f'  avg_len   {prev_avg_len:.4f} → {avg_len:.4f}  ({l_delta:+.4f})')
    print(f'  improvements={len(improved_nodes):,}  regressions={len(regressed_nodes):,}')
    for n, old, new in improved_nodes[:5]:
        print(f'    n={n:>7}  {test_metric} {old} → {new}')
    print()
    
    for node_number, old_score, new_score in improved_nodes[:5]:
        print(f'  number={node_number:>7}  {test_metric} {old_score} → {new_score}')
    print()

for strategy_name in NEW_STRATEGIES:
    del STRATEGIES[strategy_name]