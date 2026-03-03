"""SQLite database for storing optimal builtin-only expressions for integers.

Each number stores HOW it was built (strategy + parent), so improvements
to a parent automatically cascade to all its dependents.
"""

import sqlite3
import os

from anchors import BASE_ANCHORS

DB_PATH = os.path.join(os.path.dirname(__file__), 'expressions.db')

# ── Strategy registry ────────────────────────────────────────────────────
# Maps strategy name → function that builds expr from parent expr + offset.

def _apply_strategy(strategy, parent_expr, offset):
    """Given a strategy name, parent expression, and offset, build the full expression."""
    if strategy == 'base':
        return parent_expr  # parent_expr IS the expression for base anchors

    # Apply the core operation
    if strategy == 'triple':
        expr = f'len(str(list(bytes({parent_expr}))))'
    elif strategy == 'decrement':
        expr = parent_expr  # offset handles the decrementing
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
    elif strategy == 'bool_collapse':
        expr = f'int(bool({parent_expr}))'
    elif strategy == 'log_step_down':
        expr = f'len(str({parent_expr}))'
    elif strategy == 'list_range_repr_len':
        expr = f'len(str(list(range({parent_expr}))))'
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Apply decrements
    for _ in range(offset):
        expr = f'max(range({expr}))'

    return expr


# ── Database operations ──────────────────────────────────────────────────

def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create the table if it doesn't exist."""
    with get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numbers (
                n INTEGER PRIMARY KEY,
                expr TEXT NOT NULL,
                depth INTEGER NOT NULL,
                strategy TEXT NOT NULL,
                parent INTEGER,
                offset INTEGER DEFAULT 0
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_parent ON numbers(parent)')


def get(n):
    """Look up a number. Returns dict or None."""
    with get_conn() as conn:
        row = conn.execute(
            'SELECT n, expr, depth, strategy, parent, offset FROM numbers WHERE n = ?',
            (n,)
        ).fetchone()
    if row is None:
        return None
    return {
        'n': row[0], 'expr': row[1], 'depth': row[2],
        'strategy': row[3], 'parent': row[4], 'offset': row[5],
    }


def dependents(n):
    """Find all numbers whose expression depends on n."""
    with get_conn() as conn:
        rows = conn.execute(
            'SELECT n FROM numbers WHERE parent = ?', (n,)
        ).fetchall()
    return [r[0] for r in rows]


def _upsert(conn, n, expr, depth, strategy, parent, offset):
    """Insert or update if the new depth is better."""
    existing = conn.execute('SELECT depth FROM numbers WHERE n = ?', (n,)).fetchone()
    if existing is None or depth < existing[0]:
        conn.execute('''
            INSERT INTO numbers (n, expr, depth, strategy, parent, offset)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(n) DO UPDATE SET
                expr=excluded.expr,
                depth=excluded.depth,
                strategy=excluded.strategy,
                parent=excluded.parent,
                offset=excluded.offset
        ''', (n, expr, depth, strategy, parent, offset))
        return True
    return False


def improve(n, expr, depth, strategy, parent, offset):
    """Try to improve n's expression. If better, update and cascade."""
    with get_conn() as conn:
        if _upsert(conn, n, expr, depth, strategy, parent, offset):
            conn.commit()
            cascade(n)
            return True
    return False


def cascade(n):
    """When n improves, rebuild all its dependents and recurse."""
    entry = get(n)
    if entry is None:
        return

    deps = dependents(n)
    if not deps:
        return

    with get_conn() as conn:
        for dep_n in deps:
            dep = conn.execute(
                'SELECT strategy, parent, offset FROM numbers WHERE n = ?',
                (dep_n,)
            ).fetchone()
            if dep is None:
                continue
            dep_strategy, dep_parent, dep_offset = dep

            # Rebuild using the (now improved) parent expression
            new_expr = _apply_strategy(dep_strategy, entry['expr'], dep_offset)
            new_depth = new_expr.count('(')

            if _upsert(conn, dep_n, new_expr, new_depth, dep_strategy, dep_parent, dep_offset):
                conn.commit()
                cascade(dep_n)  # recurse


# ── Populate ─────────────────────────────────────────────────────────────

def populate(max_n=155_000):
    """Fill the database using the base-3 algorithm, recording decomposition."""
    init_db()

    with get_conn() as conn:
        # Base anchors
        for n, expr in BASE_ANCHORS.items():
            depth = expr.count('(')
            _upsert(conn, n, expr, depth, 'base', None, 0)

        # Numbers reachable by decrementing from a base anchor
        sorted_anchors = sorted(BASE_ANCHORS.keys())
        for i, anchor in enumerate(sorted_anchors):
            # Fill gaps between this anchor and the previous one
            prev = sorted_anchors[i - 1] + 1 if i > 0 else 0
            for n in range(prev, anchor):
                if n in BASE_ANCHORS:
                    continue
                # Find nearest anchor above
                gap = anchor - n
                expr = BASE_ANCHORS[anchor]
                for _ in range(gap):
                    expr = f'max(range({expr}))'
                depth = expr.count('(')
                _upsert(conn, n, expr, depth, 'decrement', anchor, gap)

        # Everything above max anchor via base-3 decomposition
        max_anchor = max(BASE_ANCHORS.keys())
        for n in range(max_anchor + 1, max_n + 1):
            _build_and_store(conn, n)

        conn.commit()

    count = 0
    with get_conn() as conn:
        count = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
    print(f"Populated {count} entries (0 to {max_n})")


def _build_and_store(conn, n):
    """Build n via base-3 decomposition, store in db."""
    existing = conn.execute('SELECT depth FROM numbers WHERE n = ?', (n,)).fetchone()
    if existing is not None:
        return

    if n in BASE_ANCHORS:
        _upsert(conn, n, BASE_ANCHORS[n], BASE_ANCHORS[n].count('('), 'base', None, 0)
        return

    # Base-3: n = 3*ceil(n/3) - r, where r ∈ {0, 1, 2}
    q = -(-n // 3)  # ceil(n/3)
    r = 3 * q - n

    # Ensure parent is stored first
    _build_and_store(conn, q)

    # Get parent's expression
    parent_row = conn.execute('SELECT expr FROM numbers WHERE n = ?', (q,)).fetchone()
    parent_expr = parent_row[0]

    # Build expression
    expr = f'len(str(list(bytes({parent_expr}))))'
    for _ in range(r):
        expr = f'max(range({expr}))'

    depth = expr.count('(')
    _upsert(conn, n, expr, depth, 'triple', q, r)


# ── Stats ────────────────────────────────────────────────────────────────

def stats():
    """Print coverage and depth distribution."""
    with get_conn() as conn:
        total = conn.execute('SELECT COUNT(*) FROM numbers').fetchone()[0]
        max_depth = conn.execute('SELECT MAX(depth) FROM numbers').fetchone()[0]
        avg_depth = conn.execute('SELECT AVG(depth) FROM numbers').fetchone()[0]
        min_n = conn.execute('SELECT MIN(n) FROM numbers').fetchone()[0]
        max_n = conn.execute('SELECT MAX(n) FROM numbers').fetchone()[0]

        print(f"Entries: {total}")
        print(f"Range: {min_n} to {max_n}")
        print(f"Depth: avg={avg_depth:.1f}, max={max_depth}")

        # Strategy breakdown
        print("\nBy strategy:")
        for row in conn.execute(
            'SELECT strategy, COUNT(*), AVG(depth) FROM numbers GROUP BY strategy ORDER BY COUNT(*) DESC'
        ):
            print(f"  {row[0]:<25} {row[1]:>6} entries  avg depth {row[2]:.1f}")

        # Depth histogram
        print("\nDepth distribution:")
        for row in conn.execute('''
            SELECT
                CASE
                    WHEN depth <= 10 THEN '  0-10'
                    WHEN depth <= 20 THEN ' 11-20'
                    WHEN depth <= 40 THEN ' 21-40'
                    WHEN depth <= 60 THEN ' 41-60'
                    WHEN depth <= 80 THEN ' 61-80'
                    WHEN depth <= 100 THEN ' 81-100'
                    ELSE '100+'
                END as bucket,
                COUNT(*)
            FROM numbers
            GROUP BY bucket
            ORDER BY bucket
        '''):
            print(f"  {row[0]}: {row[1]:>6}")


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        stats()
    else:
        populate()
        stats()
