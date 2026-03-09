"""Test a new strategy against the database.

Usage: paste your forward function and inverse function below, then run.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.optimize import load_entries, find_improvements, MAX_N
from core.db import init_db, STRATEGIES as DB_STRATEGIES

MAX_OFFSET = 2

# ┌─────────────────────────────────────────────────────────┐
# │  PASTE YOUR STRATEGY HERE                               │
# └─────────────────────────────────────────────────────────┘

STRATEGY_NAME = 'my_new_strategy'

def forward(parent_expr):
    """Takes a parent expression string, returns the new expression string."""
    return f'len(str(list(bytes({parent_expr}))))'  # <-- replace this

def inverse(target):
    """Takes a target number, returns (parent, offset) or None."""
    for offset in range(MAX_OFFSET + 1):
        val = target + offset
        if val > 0 and val % 3 == 0:  # <-- replace this
            parent = val // 3
            if parent >= 1:
                return parent, offset
    return None

# ┌─────────────────────────────────────────────────────────┐
# │  DON'T EDIT BELOW                                       │
# └─────────────────────────────────────────────────────────┘

DB_STRATEGIES[STRATEGY_NAME] = lambda p: forward(p)

init_db()
entries = load_entries()
results = find_improvements(entries, MAX_N, strategies=[(STRATEGY_NAME, inverse)])

print(f'\nStrategy: {STRATEGY_NAME}')
print(f'Improvements: {len(results)} / {len(entries)} numbers')

if results[:5]:
    print(f'\nExamples (first 5):')
    for candidate, new_depth, length, name, parent_n, offset, target in results[:5]:
        print(f'  n={target}: depth -> {new_depth}')

if not results:
    print('No improvements found.')
