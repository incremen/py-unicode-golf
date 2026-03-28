"""SQLite database for storing optimal builtin-only expressions for integers.

CLI:
    python core/db.py              — print current stats
    python core/db.py --populate   — reseed DB from base-3 algorithm (wipes existing data)
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'expressions.db')
MAX_N = 200_000


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


def bulk_write(nodes_dict):
    """Clear the numbers table and bulk-insert all entries from nodes_dict.

    nodes_dict: {n: {expr, depth, len, strategy, parent, offset}}
    """
    rows = [
        (n, d['expr'], d['depth'], d['len'], d['strategy'], d['parent'], d['offset'])
        for n, d in sorted(nodes_dict.items())
    ]
    conn = get_conn()
    conn.execute('DELETE FROM numbers')
    conn.executemany(
        'INSERT INTO numbers (n, expr, depth, len, strategy, parent, offset) VALUES (?,?,?,?,?,?,?)',
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


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
        row = conn.execute(
            'SELECT COUNT(*), AVG(depth), MAX(depth), AVG(len), MAX(len) FROM numbers'
        ).fetchone()
        total, avg_depth, max_depth, avg_len, max_len = row

        strategy_rows = conn.execute(
            'SELECT strategy, COUNT(*) FROM numbers GROUP BY strategy'
        ).fetchall()
        strategy_counts = {r[0]: r[1] for r in strategy_rows}

        conn.execute('''
            INSERT INTO optimization_log
            (timestamp, label, improvements, total_entries, avg_depth, max_depth, avg_len, max_len, strategy_counts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(), label, improvements,
            total, round(avg_depth, 4), max_depth,
            round(avg_len, 4), max_len,
            json.dumps(strategy_counts),
        ))
        conn.commit()


def get_log():
    """Return optimization history."""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT id, timestamp, label, improvements, total_entries, '
            'avg_depth, max_depth, avg_len, max_len, strategy_counts '
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
        total, avg_depth, max_depth, avg_len, max_len = conn.execute(
            'SELECT COUNT(*), AVG(depth), MAX(depth), AVG(len), MAX(len) FROM numbers'
        ).fetchone()

    print(f'Entries: {total}')
    print(f'Depth:  avg={avg_depth:.1f}  max={max_depth}')
    print(f'Length: avg={avg_len:.0f}  max={max_len}')

    log = get_log()
    if not log:
        return
    print(f'\nOptimization history ({len(log)} entries):')
    for entry in log:
        print(f"  [{entry['id']}] {entry['label']}: "
              f"avg_depth={entry['avg_depth']}, max_depth={entry['max_depth']}, "
              f"avg_len={entry['avg_len']}, improvements={entry['improvements']}")


def _insert(conn, n, expr, strategy, parent=None, offset=0):
    conn.execute(
        'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent, offset) VALUES (?,?,?,?,?,?,?)',
        (n, expr, expr.count('('), len(expr), strategy, parent, offset),
    )


def snapshot_minimal_formula(max_n=MAX_N):
    """Compute base-3 stats using only seeds 0 and 1, without touching the numbers table."""
    memo = {}
    def build(n):
        if n in memo: return memo[n]
        if n == 0: memo[0] = 'int(not(not()))'; return memo[0]
        if n == 1: memo[1] = 'int(not())';      return memo[1]
        q = -(-n // 3); r = 3 * q - n
        expr = f'len(str(list(bytes({build(q)}))))'
        for _ in range(r): expr = f'max(range({expr}))'
        memo[n] = expr; return expr

    import sys as _sys
    old_limit = _sys.getrecursionlimit()
    _sys.setrecursionlimit(100_000)
    exprs = [build(n) for n in range(max_n + 1)]
    _sys.setrecursionlimit(old_limit)

    depths = [e.count('(') for e in exprs]
    lengths = [len(e) for e in exprs]
    total = len(exprs)
    avg_d = sum(depths) / total
    avg_l = sum(lengths) / total

    with get_conn() as conn:
        strategy_counts = json.dumps({'base-3-minimal': total})
        conn.execute('''
            INSERT INTO optimization_log
            (timestamp, label, improvements, total_entries, avg_depth, max_depth, avg_len, max_len, strategy_counts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            'minimal formula (seeds: 0, 1)',
            0, total,
            round(avg_d, 4), max(depths),
            round(avg_l, 4), max(lengths),
            strategy_counts,
        ))
        conn.commit()
    print(f'Snapshotted minimal formula: avg_depth={avg_d:.4f}  max_depth={max(depths)}')


def populate(max_n=MAX_N):
    """Seed the database with base-3 expressions for all integers 0..max_n."""
    from core.anchors import BASE_ANCHORS, build_n
    from core.strategies import apply_strategy

    init_db()
    with get_conn() as conn:
        conn.execute('DELETE FROM numbers')

        # Base anchors
        for n, expr in BASE_ANCHORS.items():
            _insert(conn, n, expr, 'base')

        # Fill gaps between anchors via decrement
        sorted_anchors = sorted(BASE_ANCHORS.keys())
        for i, anchor in enumerate(sorted_anchors):
            prev = sorted_anchors[i - 1] + 1 if i > 0 else 0
            for n in range(prev, anchor):
                if n in BASE_ANCHORS:
                    continue
                gap = anchor - n
                expr = apply_strategy('decrement', BASE_ANCHORS[anchor], gap - 1)
                _insert(conn, n, expr, 'decrement', parent=anchor, offset=gap)

        # Base-3 for everything above the last anchor
        max_anchor = max(BASE_ANCHORS.keys())
        for n in range(max_anchor + 1, max_n + 1):
            if n in BASE_ANCHORS:
                continue
            _insert(conn, n, build_n(n), 'triple', parent=None, offset=0)

        conn.commit()

    with get_conn() as conn:
        count = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
    print(f'Populated {count:,} entries (0 to {max_n})')
    snapshot('base-3 (44 anchors)', improvements=0)


if __name__ == '__main__':
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    if '--populate' in sys.argv:
        populate()
    stats()
