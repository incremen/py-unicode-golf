"""Render a directed graph of integer nodes 0-N for the py-unicode-golf strategies.

Usage:
    python reference/graph.py            # renders graph_0_20.svg
    python reference/graph.py --max 30  # change node range
"""

import graphviz, sys, os, math

# ── Config ──────────────────────────────────────────────────────────────────

MAX_N = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 20
COLS  = 5          # nodes per row in the grid
SPACING = 2.5      # inches between nodes

# ── Strategies ──────────────────────────────────────────────────────────────
# (name, edge_label, forward_fn, hex_color)

STRATEGIES = [
    ('decrement',    'n−1',       lambda n: n - 1,        '#e74c3c'),
    ('triple',       '3n',        lambda n: 3 * n,         '#2ecc71'),
    ('quad_plus_3',  '4n+3',      lambda n: 4 * n + 3,     '#5dade2'),
    ('triangular',   'n(n−1)/2',  lambda n: n*(n-1)//2,    '#9b59b6'),
    ('bytearray_4x', '4n+14',     lambda n: 4 * n + 14,    '#f39c12'),
]

# ── Build graph ─────────────────────────────────────────────────────────────

g = graphviz.Digraph(name='integer_graph', format='svg', engine='neato')
g.attr(
    overlap='false', splines='curved',
    bgcolor='#12151e', fontcolor='white', fontname='Courier New',
    label=f'Integer construction graph  (nodes 0–{MAX_N})',
    fontsize='16', labelloc='b', pad='0.6',
)
g.attr('node',
    shape='circle', style='filled,bold',
    fillcolor='#2c3e50', color='#7f8c8d',
    fontcolor='white', fontname='Courier New',
    fontsize='14', width='0.75', height='0.75', fixedsize='true',
)
g.attr('edge', fontname='Courier New', fontsize='9', arrowsize='0.7')

NODES = range(MAX_N + 1)

# Place nodes in a grid using explicit pos
for n in NODES:
    row, col = divmod(n, COLS)
    x = col * SPACING
    y = -row * SPACING
    g.node(str(n), str(n), pos=f'{x},{y}!')

# Add edges, label only the first occurrence per strategy
labeled = set()
for name, lbl, fn, color in STRATEGIES:
    for n in NODES:
        t = fn(n)
        if 0 <= t <= MAX_N and t != n:
            first = name not in labeled
            if first:
                labeled.add(name)
            g.edge(
                str(n), str(t),
                label=lbl if first else '',
                color=color, fontcolor=color,
                penwidth='2.0',
            )

# Legend
with g.subgraph(name='cluster_legend') as leg:
    leg.attr(
        label='Strategies', style='filled',
        fillcolor='#1a1e28', color='#4a5568',
        fontcolor='white', fontname='Courier New', fontsize='11',
    )
    prev = None
    for name, lbl, fn, color in STRATEGIES:
        # Find one example edge
        for n in NODES:
            t = fn(n)
            if 0 <= t <= MAX_N and t != n:
                example = f'e.g. {n}→{t}'
                break
        full = f'{lbl}  ({example})'
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
