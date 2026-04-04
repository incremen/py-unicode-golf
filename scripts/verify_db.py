"""Verify that every expression stored in the DB evaluates to the correct integer.

CLI:
    python scripts/verify_db.py          — verify all entries
    python scripts/verify_db.py 1000     — verify first N entries (for quick testing)
"""

import sys
from multiprocessing import Pool, cpu_count
from core.db import get_conn
from core.config import STORE_N


def check_row(args):
    n, expr = args
    try:
        result = eval(expr)
        if result != n:
            return (n, expr, f'got {result!r}')
    except Exception as e:
        return (n, expr, str(e))
    return None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else STORE_N

    with get_conn() as conn:
        rows = conn.execute(
            'SELECT n, expr FROM numbers WHERE n <= ? ORDER BY n', (limit,)
        ).fetchall()

    print(f'Verifying {len(rows):,} entries across {cpu_count()} cores...')

    with Pool() as pool:
        results = pool.map(check_row, rows, chunksize=500)

    failures = [r for r in results if r is not None]

    if failures:
        print(f'FAILED: {len(failures)} entries')
        for n, expr, reason in failures[:20]:
            print(f'  n={n}: {reason}  expr={expr}')
    else:
        print(f'All {len(rows):,} entries OK')


if __name__ == '__main__':
    main()
