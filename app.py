"""Flask web app for pyfuncs_to_chars."""

import os
import json
from flask import Flask, jsonify, send_from_directory
from anchors import build_n, build_char, BASE_ANCHORS

app = Flask(__name__, static_folder='static')

# Load optimized expressions from JSON (works on Vercel) or SQLite (local dev)
DB_EXPRS = None
DB_AVAILABLE = False

def _load_db():
    global DB_EXPRS, DB_AVAILABLE
    json_path = os.path.join(os.path.dirname(__file__), 'expressions.json')
    db_path = os.path.join(os.path.dirname(__file__), 'expressions.db')

    if os.path.exists(json_path):
        with open(json_path) as f:
            DB_EXPRS = json.load(f)
        DB_AVAILABLE = True
    elif os.path.exists(db_path):
        from db import get_conn
        conn = get_conn()
        rows = conn.execute('SELECT n, expr FROM numbers').fetchall()
        conn.close()
        DB_EXPRS = {str(r[0]): r[1] for r in rows}
        DB_AVAILABLE = True

_load_db()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/char/<path:char>')
def api_char(char):
    if len(char) != 1:
        return jsonify({'error': 'Expected exactly one character'}), 400

    code_point = ord(char)
    formula_expr = build_char(char)

    result = {
        'char': char,
        'code_point': code_point,
        'formula': {
            'expr': formula_expr,
            'depth': formula_expr.count('('),
            'len': len(formula_expr),
        },
    }

    if DB_AVAILABLE and str(code_point) in DB_EXPRS:
        inner = DB_EXPRS[str(code_point)]
        expr = f"chr({inner})"
        result['db'] = {
            'expr': expr,
            'depth': expr.count('('),
            'len': len(expr),
        }

    return jsonify(result)


@app.route('/api/log')
def api_log():
    db_path = os.path.join(os.path.dirname(__file__), 'expressions.db')
    if os.path.exists(db_path):
        from db import get_log
        return jsonify(get_log())
    return jsonify([])


@app.route('/api/stats')
def api_stats():
    if not DB_AVAILABLE:
        return jsonify({'total': 0, 'avg_depth': 0, 'max_depth': 0, 'avg_len': 0, 'max_len': 0, 'strategies': []})

    exprs = list(DB_EXPRS.values())
    depths = [e.count('(') for e in exprs]
    lengths = [len(e) for e in exprs]
    return jsonify({
        'total': len(exprs),
        'avg_depth': round(sum(depths) / len(depths), 2),
        'max_depth': max(depths),
        'avg_len': round(sum(lengths) / len(lengths), 1),
        'max_len': max(lengths),
        'strategies': [],  # not available from JSON
    })


@app.route('/api/formula-stats')
def api_formula_stats():
    sample = list(range(0, 200_001, 10))
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
    return jsonify({str(k): v for k, v in sorted(BASE_ANCHORS.items())})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
