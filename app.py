"""Flask web app for pyfuncs_to_chars."""

from flask import Flask, jsonify, send_from_directory
from anchors import build_n, build_char, BASE_ANCHORS
from db import get, get_log, get_conn, init_db

app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/char/<path:char>')
def api_char(char):
    """Get expression for a character. Uses formula by default, db if requested."""
    if len(char) != 1:
        return jsonify({'error': 'Expected exactly one character'}), 400

    code_point = ord(char)

    # Formula result (always available)
    formula_expr = build_char(char)
    formula_depth = formula_expr.count('(')

    result = {
        'char': char,
        'code_point': code_point,
        'formula': {
            'expr': formula_expr,
            'depth': formula_depth,
            'len': len(formula_expr),
        },
    }

    # DB result (if available)
    db_entry = get(code_point)
    if db_entry:
        result['db'] = {
            'expr': f"chr({db_entry['expr']})",
            'depth': db_entry['depth'] + 1,  # +1 for chr()
            'len': db_entry['len'] + 5,       # chr( + )
            'strategy': db_entry['strategy'],
            'parent': db_entry['parent'],
        }

    return jsonify(result)


@app.route('/api/log')
def api_log():
    """Get optimization history."""
    return jsonify(get_log())


@app.route('/api/stats')
def api_stats():
    """Get current database stats."""
    conn = get_conn()
    row = conn.execute('''
        SELECT COUNT(*), AVG(depth), MAX(depth), AVG(len), MAX(len)
        FROM numbers
    ''').fetchone()
    strategies = conn.execute(
        'SELECT strategy, COUNT(*), AVG(depth) FROM numbers GROUP BY strategy ORDER BY COUNT(*) DESC'
    ).fetchall()
    conn.close()

    return jsonify({
        'total': row[0],
        'avg_depth': round(row[1], 2) if row[1] else 0,
        'max_depth': row[2] or 0,
        'avg_len': round(row[3], 1) if row[3] else 0,
        'max_len': row[4] or 0,
        'strategies': [
            {'name': s[0], 'count': s[1], 'avg_depth': round(s[2], 1)}
            for s in strategies
        ],
    })


@app.route('/api/formula-stats')
def api_formula_stats():
    """Stats for the base-3 formula across a sample of code points."""
    import random
    random.seed(0)
    sample = list(range(0, 200_001, 10))  # every 10th
    depths = []
    lengths = []
    for n in sample:
        expr = f'chr({build_n(n)})'
        depths.append(expr.count('('))
        lengths.append(len(expr))
    return jsonify({
        'sample_size': len(sample),
        'avg_depth': round(sum(depths) / len(depths), 1),
        'max_depth': max(depths),
        'avg_len': round(sum(lengths) / len(lengths), 1),
        'max_len': max(lengths),
    })


@app.route('/api/anchors')
def api_anchors():
    """Get base anchors."""
    return jsonify({str(k): v for k, v in sorted(BASE_ANCHORS.items())})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
