"""SQLite database for storing optimal builtin-only expressions for integers.

Each number stores HOW it was built (strategy + parent), so improvements
to a parent automatically cascade to all its dependents.

Tracks optimization history so you can compare before/after.
"""

import sqlite3
import json
import os
from datetime import datetime

from anchors import BASE_ANCHORS

DB_PATH = os.path.join(os.path.dirname(__file__), 'expressions.db')
MAX_N = 200_000


# ── Strategy application ─────────────────────────────────────────────────

def apply_strategy(strategy, parent_expr, offset):
    """Given a strategy name, parent expression, and offset, build the full expression."""
    if strategy == 'base':
        expr = parent_expr
    elif strategy == 'triple':
        expr = f'len(str(list(bytes({parent_expr}))))'
    elif strategy == 'decrement':
        expr = parent_expr
    elif strategy == 'quad_plus_3':
        expr = f'len(str(bytes({parent_expr})))'
    elif strategy == 'quint_plus_5':
        expr = f'len(ascii(str(bytes({parent_expr}))))'
    elif strategy.startswith('ascii_exp_'):
        k = int(strategy.split('_')[-1])
        inner = f'str(bytes({parent_expr}))'
        for _ in range(k):
            inner = f'ascii({inner})'
        expr = f'len({inner})'
    elif strategy.startswith('zip_chain_'):
        k = int(strategy.split('_')[-1])
        inner = f'bytes({parent_expr})'
        for _ in range(k):
            inner = f'zip({inner})'
        expr = f'len(str(list({inner})))'
    elif strategy == 'triangular':
        expr = f'sum(range({parent_expr}))'
    elif strategy == 'enum_list_8x':
        expr = f'len(str(list(enumerate(bytes({parent_expr})))))'
    elif strategy == 'slice_offset':
        expr = f'len(str(slice({parent_expr})))'
    elif strategy == 'complex_offset':
        expr = f'len(str(complex({parent_expr})))'
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    for _ in range(offset):
        expr = f'max(range({expr}))'
    return expr


# ── Database operations ──────────────────────────────────────────────────

def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numbers (
                n INTEGER PRIMARY KEY,
                expr TEXT NOT NULL,
                depth INTEGER NOT NULL,
                len INTEGER NOT NULL,
                strategy TEXT NOT NULL,
                parent INTEGER,
                offset INTEGER DEFAULT 0
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_parent ON numbers(parent)')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS optimization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                label TEXT NOT NULL,
                improvements INTEGER NOT NULL,
                total_entries INTEGER NOT NULL,
                avg_depth REAL NOT NULL,
                max_depth INTEGER NOT NULL,
                avg_len REAL NOT NULL,
                max_len INTEGER NOT NULL,
                strategy_counts TEXT NOT NULL
            )
        ''')


def get(n):
    """Look up a number. Returns dict or None."""
    with get_conn() as conn:
        row = conn.execute(
            'SELECT n, expr, depth, len, strategy, parent, offset FROM numbers WHERE n = ?',
            (n,)
        ).fetchone()
    if row is None:
        return None
    return {
        'n': row[0], 'expr': row[1], 'depth': row[2], 'len': row[3],
        'strategy': row[4], 'parent': row[5], 'offset': row[6],
    }


def dependents(n):
    """Find all numbers whose expression depends on n."""
    with get_conn() as conn:
        rows = conn.execute('SELECT n FROM numbers WHERE parent = ?', (n,)).fetchall()
    return [r[0] for r in rows]


def snapshot(label, improvements=0):
    """Record current database stats to optimization_log."""
    with get_conn() as conn:
        stats = conn.execute('''
            SELECT COUNT(*), AVG(depth), MAX(depth), AVG(len), MAX(len)
            FROM numbers
        ''').fetchone()
        total, avg_depth, max_depth, avg_len, max_len = stats

        strategy_rows = conn.execute(
            'SELECT strategy, COUNT(*) FROM numbers GROUP BY strategy'
        ).fetchall()
        strategy_counts = {r[0]: r[1] for r in strategy_rows}

        conn.execute('''
            INSERT INTO optimization_log
            (timestamp, label, improvements, total_entries, avg_depth, max_depth, avg_len, max_len, strategy_counts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            label,
            improvements,
            total,
            round(avg_depth, 2),
            max_depth,
            round(avg_len, 2),
            max_len,
            json.dumps(strategy_counts),
        ))
        conn.commit()


def get_log():
    """Return optimization history."""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT id, timestamp, label, improvements, total_entries, avg_depth, max_depth, avg_len, max_len, strategy_counts '
            'FROM optimization_log ORDER BY id'
        ).fetchall()
    return [{
        'id': r[0], 'timestamp': r[1], 'label': r[2],
        'improvements': r[3], 'total_entries': r[4],
        'avg_depth': r[5], 'max_depth': r[6],
        'avg_len': r[7], 'max_len': r[8],
        'strategy_counts': json.loads(r[9]),
    } for r in rows]


def stats():
    """Print current stats and history."""
    with get_conn() as conn:
        total = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
        avg_depth = conn.execute('SELECT AVG(depth) FROM numbers').fetchone()[0]
        max_depth = conn.execute('SELECT MAX(depth) FROM numbers').fetchone()[0]
        avg_len = conn.execute('SELECT AVG(len) FROM numbers').fetchone()[0]
        max_len = conn.execute('SELECT MAX(len) FROM numbers').fetchone()[0]

    print(f"Entries: {total}")
    print(f"Depth:  avg={avg_depth:.1f}  max={max_depth}")
    print(f"Length: avg={avg_len:.0f}  max={max_len}")

    log = get_log()
    if log:
        print(f"\nOptimization history ({len(log)} entries):")
        for entry in log:
            print(f"  [{entry['id']}] {entry['label']}: "
                  f"avg_depth={entry['avg_depth']}, max_depth={entry['max_depth']}, "
                  f"avg_len={entry['avg_len']}, improvements={entry['improvements']}")


# ── Populate ─────────────────────────────────────────────────────────────

def populate(max_n=MAX_N):
    """Fill the database with the base-3 algorithm."""
    init_db()

    with get_conn() as conn:
        # Base anchors
        for n, expr in BASE_ANCHORS.items():
            conn.execute(
                'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent, offset) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (n, expr, expr.count('('), len(expr), 'base', None, 0)
            )

        # Fill gaps between anchors by decrementing
        sorted_anchors = sorted(BASE_ANCHORS.keys())
        for i, anchor in enumerate(sorted_anchors):
            prev = sorted_anchors[i - 1] + 1 if i > 0 else 0
            for n in range(prev, anchor):
                if n in BASE_ANCHORS:
                    continue
                gap = anchor - n
                expr = BASE_ANCHORS[anchor]
                for _ in range(gap):
                    expr = f'max(range({expr}))'
                conn.execute(
                    'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent, offset) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (n, expr, expr.count('('), len(expr), 'decrement', anchor, gap)
                )

        # Everything above max anchor via base-3
        max_anchor = max(sorted_anchors)
        memo = {}
        for n_val, expr_val in BASE_ANCHORS.items():
            memo[n_val] = expr_val

        def build(n):
            if n in memo:
                return memo[n]
            q = -(-n // 3)
            r = 3 * q - n
            parent_expr = build(q)
            expr = f'len(str(list(bytes({parent_expr}))))'
            for _ in range(r):
                expr = f'max(range({expr}))'
            memo[n] = expr
            return expr

        for n in range(max_anchor + 1, max_n + 1):
            if n in BASE_ANCHORS:
                continue
            q = -(-n // 3)
            r = 3 * q - n
            expr = build(n)
            conn.execute(
                'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent, offset) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (n, expr, expr.count('('), len(expr), 'triple', q, r)
            )

        conn.commit()

    count = 0
    with get_conn() as conn:
        count = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
    print(f"Populated {count} entries (0 to {max_n})")
    snapshot('initial (base-3)', improvements=0)


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        stats()
    else:
        populate()
        stats()
