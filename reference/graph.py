"""Render a directed graph of integer nodes 0-N for the py-unicode-golf strategies.

Each strategy is a colored edge type. Nodes are labeled with their value.
Edge labels show a short form on the first occurrence of each strategy.

Usage:
    python reference/graph.py            # renders graph_0_20.svg
    python reference/graph.py --max 50  # change node range
    pip install graphviz                 # also needs graphviz binaries installed
"""

import graphviz
import sys
import os

# ── Configuration ──────────────────────────────────────────────────────────

MAX_N = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 20

# ── Strategies ──────────────────────────────────────────────────────────────
# Each entry: (name, short_label, python_expr, forward_fn, color)

STRATEGIES = [
    ('decrement',    'n−1',        'max(range(n)) = n−1',              lambda n: n - 1,        '#e74c3c'),
    ('triple',       '3n',         'len(str(list(bytes(n)))) = 3n',    lambda n: 3 * n,         '#2ecc71'),
    ('quad_plus_3',  '4n+3',       'len(str(bytes(n))) = 4n+3',        lambda n: 4 * n + 3,     '#3498db'),
    ('triangular',   'n(n−1)/2',   'sum(range(n)) = n(n−1)/2',        lambda n: n*(n-1)//2,    '#9b59b6'),
    ('bytearray_4x', '4n+14',      'len(str(bytearray(n))) = 4n+14',  lambda n: 4 * n + 14,    '#f39c12'),
]

NODES = range(MAX_N + 1)

# ── Build graph ─────────────────────────────────────────────────────────────

g = graphviz.Digraph(name='integer_graph', format='svg')
g.attr(rankdir='LR', fontname='Courier New', bgcolor='#12151e',
       label=f'Integer construction graph  (nodes 0–{MAX_N})',
       fontcolor='white', fontsize='14', pad='0.5', nodesep='0.4', ranksep='1.2')
g.attr('node', shape='circle', style='filled', fillcolor='#1a1e28',
       color='#4a5568', fontcolor='white', fontname='Courier New', fontsize='11', width='0.45')
g.attr('edge', fontname='Courier New', fontsize='8', arrowsize='0.6')

# nodes
for n in NODES:
    g.node(str(n), str(n))

# edges — label only the first occurrence of each strategy to avoid clutter
labeled = set()
for name, short, full, fn, color in STRATEGIES:
    for n in NODES:
        t = fn(n)
        if 0 <= t <= MAX_N and t != n:
            first = name not in labeled
            if first:
                labeled.add(name)
            g.edge(str(n), str(t),
                   label=short if first else '',
                   color=color, fontcolor=color,
                   penwidth='1.8' if first else '1.2')

# legend subgraph
with g.subgraph(name='cluster_legend') as leg:
    leg.attr(label='Strategies', style='filled', fillcolor='#1a1e28',
             color='#4a5568', fontcolor='white', fontname='Courier New', fontsize='11')
    prev = None
    for name, short, full, fn, color in STRATEGIES:
        leg.node(f'leg_{name}', full,
                 shape='plaintext', fontcolor=color,
                 style='', fillcolor='transparent', width='0', height='0.3')
        if prev:
            leg.edge(f'leg_{prev}', f'leg_{name}', style='invis')
        prev = name

# ── Render ──────────────────────────────────────────────────────────────────

out = os.path.join(os.path.dirname(__file__), f'graph_0_{MAX_N}')
g.render(out, view=True, cleanup=True)
print(f'Rendered → {out}.svg')
