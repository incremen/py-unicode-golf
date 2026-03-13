"""Flask web app for py-unicode-golf"""

import os
import json
import unicodedata
from urllib.parse import unquote
from flask import Flask, jsonify, send_from_directory, request
from core.anchors import build_char, build_string, BASE_ANCHORS
from core.visualize import evaluate_steps, evaluate_string_steps

app = Flask(__name__, static_folder='static')
MAX_STRING_LENGTH = 200
# Load optimized expressions from JSON (works on Vercel) or SQLite (local dev)
DB_EXPRS = None
DB_AVAILABLE = False

def load_db():
    global DB_EXPRS, DB_AVAILABLE
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base, 'expressions.json')
        db_path = os.path.join(base, 'expressions.db')

        if os.path.exists(json_path):
            with open(json_path) as f:
                DB_EXPRS = json.load(f)
            DB_AVAILABLE = True
        elif os.path.exists(db_path):
            from core.db import get_conn
            conn = get_conn()
            rows = conn.execute('SELECT n, expr FROM numbers').fetchall()
            conn.close()
            DB_EXPRS = {str(r[0]): r[1] for r in rows}
            DB_AVAILABLE = True
    except Exception as e:
        print(f"Warning: could not load db: {e}")

load_db()


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/char/<path:char>')
@app.route('/api/char')
def api_char(char=None):
    if char is None:
        char = request.args.get('c', '')
    else:
        char = unquote(char)
    if len(char) != 1:
        return jsonify({'error': f'Expected exactly one character, got {len(char)} ({repr(char)})'}), 400

    code_point = ord(char)
    formula_expr = build_char(char)

    try:
        name = unicodedata.name(char)
    except ValueError:
        name = None

    result = {
        'char': char,
        'code_point': code_point,
        'name': name,
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


@app.route('/api/expr/<path:char>')
@app.route('/api/expr')
def api_expr(char=None):
    if char is None:
        char = request.args.get('c', '')
    else:
        char = unquote(char)
    if len(char) != 1:
        return f'Expected exactly one character, got {len(char)} ({repr(char)})', 400

    code_point = ord(char)
    if DB_AVAILABLE and str(code_point) in DB_EXPRS:
        return f"chr({DB_EXPRS[str(code_point)]})", 200, {'Content-Type': 'text/plain'}

    return build_char(char), 200, {'Content-Type': 'text/plain'}


@app.route('/api/log')
def api_log():
    db_path = os.path.join(os.path.dirname(__file__), 'expressions.db')
    if os.path.exists(db_path):
        from core.db import get_log
        return jsonify(get_log())
    return jsonify([])


@app.route('/api/anchors')
def api_anchors():
    return jsonify({str(k): v for k, v in sorted(BASE_ANCHORS.items())})


@app.route('/api/string')
def api_string():
    text = request.args.get('s', '')
    if not text:
        return jsonify({'error': 'Missing s parameter'}), 400
    if len(text) > MAX_STRING_LENGTH:
        return jsonify({'error': f'Max {MAX_STRING_LENGTH} characters'}), 400

    expr = build_string(text)
    return jsonify({
        'text': text,
        'expr': expr,
        'depth': expr.count('('),
        'len': len(expr),
    })


@app.route('/api/visualize')
def api_visualize():
    expr = request.args.get('expr', '')
    if not expr:
        return jsonify({'error': 'Missing expr parameter'}), 400
    return jsonify({'steps': evaluate_steps(expr)})


@app.route('/api/visualize_string')
def api_visualize_string():
    text = request.args.get('s', '')
    if not text or len(text) > MAX_STRING_LENGTH:
        return jsonify({'error': 'Invalid string'}), 400
    return jsonify(evaluate_string_steps(text))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
