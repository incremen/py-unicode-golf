"""SQLite database for storing optimal builtin-only expressions for integers.

CLI:
    python core/db.py              — print current stats
    python core/db.py --populate   — reseed DB from base-3 algorithm (wipes existing data)
"""

import sqlite3
import json
import os
from datetime import datetime

from core.config import MAX_N

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'expressions.db')


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
                expr_len TEXT,
                depth_len INTEGER,
                len_len INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_parent ON numbers(parent)')
        existing = {r[1] for r in conn.execute('PRAGMA table_info(numbers)').fetchall()}
        for col, typedef in [('expr_len', 'TEXT'), ('depth_len', 'INTEGER'), ('len_len', 'INTEGER')]:
            if col not in existing:
                conn.execute(f'ALTER TABLE numbers ADD COLUMN {col} {typedef}')
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


def merge_best(graph, metric, write=True):
    """Update DB entries only where graph found a strictly better representation.

    metric: 'depth' compares graph[n]['depth'] vs numbers.depth
            'length' compares graph[n]['len']   vs numbers.len_len
    Returns (improved, regressed) lists of (n, old_val, new_val).
    """
    conn = get_conn()
    if metric == 'depth':
        current = {r[0]: (r[1], r[2]) for r in conn.execute('SELECT n, depth, len FROM numbers').fetchall()}
    else:
        current = {r[0]: (r[1], r[2]) for r in conn.execute('SELECT n, len_len, depth_len FROM numbers').fetchall()}

    improved, regressed, updates, inserts = [], [], [], []
    for n, node in graph.items():
        new_primary   = node['depth'] if metric == 'depth' else node['len']
        new_secondary = node['len']   if metric == 'depth' else node['depth']

        if n not in current:
            inserts.append((n, node['expr'], node['depth'], node['len'], node['strategy'], node['parent']))
            improved.append((n, None, new_primary))
            continue

        old_primary, old_secondary = current[n]
        if old_primary is None or new_primary < old_primary or (new_primary == old_primary and new_secondary < (old_secondary or float('inf'))):
            improved.append((n, old_primary, new_primary))
            if metric == 'depth':
                updates.append((node['expr'], node['depth'], node['len'], node['strategy'], node['parent'], n))
            else:
                updates.append((node['expr'], node['depth'], node['len'], n))
        elif new_primary > (old_primary or 0):
            regressed.append((n, old_primary, new_primary))

    if write:
        if inserts:
            conn.executemany(
                'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent) VALUES (?,?,?,?,?,?)', inserts)
        if updates:
            if metric == 'depth':
                conn.executemany('UPDATE numbers SET expr=?, depth=?, len=?, strategy=?, parent=? WHERE n=?', updates)
            else:
                conn.executemany('UPDATE numbers SET expr_len=?, depth_len=?, len_len=? WHERE n=?', updates)
        conn.commit()
    conn.close()
    return improved, regressed


def bulk_write(depth_dict, length_dict=None):
    """Clear the numbers table and bulk-insert both optimized representations.

    depth_dict:  {n: {expr, depth, len, strategy, parent}}  — depth-optimized (required)
    length_dict: {n: {expr, depth, len, strategy, parent}}  — length-optimized (optional)
    """
    rows = []
    for n, d in sorted(depth_dict.items()):
        l = length_dict.get(n) if length_dict else None
        rows.append((
            n, d['expr'], d['depth'], d['len'], d['strategy'], d['parent'],
            l['expr'] if l else None,
            l['depth'] if l else None,
            l['len'] if l else None,
        ))
    conn = get_conn()
    conn.execute('DELETE FROM numbers')
    conn.executemany(
        'INSERT INTO numbers (n, expr, depth, len, strategy, parent, expr_len, depth_len, len_len) VALUES (?,?,?,?,?,?,?,?,?)',
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def get(n):
    """Look up a number. Returns dict or None."""
    with get_conn() as conn:
        row = conn.execute(
            'SELECT n, expr, depth, len, strategy, parent, expr_len, depth_len, len_len FROM numbers WHERE n = ?',
            (n,)
        ).fetchone()
    if row is None:
        return None
    result = {
        'n': row[0], 'expr': row[1], 'depth': row[2], 'len': row[3],
        'strategy': row[4], 'parent': row[5],
    }
    if row[6] is not None:
        result['expr_len']   = row[6]
        result['depth_len']  = row[7]
        result['len_len']    = row[8]
    return result


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


JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'expressions.json')

def generate_json():
    """Export expressions to expressions.json for Vercel deployment."""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT n, expr, expr_len FROM numbers ORDER BY n'
        ).fetchall()
    data = {}
    for n, expr_depth, expr_length in rows:
        data[str(n)] = {'depth': expr_depth, 'length': expr_length} if expr_length else expr_depth
    with open(JSON_PATH, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'Exported {len(data):,} entries to expressions.json')


def _insert(conn, n, expr, strategy, parent=None):
    conn.execute(
        'INSERT OR IGNORE INTO numbers (n, expr, depth, len, strategy, parent) VALUES (?,?,?,?,?,?)',
        (n, expr, expr.count('('), len(expr), strategy, parent),
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
    from core.anchors import BASE_ANCHORS
from core.build_base_3 import build_n
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
                _insert(conn, n, expr, 'decrement', parent=anchor)

        # Base-3 for everything above the last anchor
        max_anchor = max(BASE_ANCHORS.keys())
        for n in range(max_anchor + 1, max_n + 1):
            if n in BASE_ANCHORS:
                continue
            _insert(conn, n, build_n(n), 'triple', parent=None)

        conn.commit()

    with get_conn() as conn:
        count = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
    print(f'Populated {count:,} entries (0 to {max_n})')
    snapshot('base-3 (44 anchors)', improvements=0)


if __name__ == '__main__':
    import sys, os as _os
    if '--populate' in sys.argv:
        populate()
    stats()
