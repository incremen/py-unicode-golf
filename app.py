"""Flask web app for py-unicode-golf"""

import os
import sys
import json
import unicodedata
from urllib.parse import unquote
from flask import Flask, jsonify, send_from_directory, request
from core.anchors import build_char, build_string, build_n, BASE_ANCHORS
from core.compile import compile_payload_stealth
from core.visualize import evaluate_steps, evaluate_string_steps

app = Flask(__name__, static_folder='static')
MAX_STRING_LENGTH = 200
# Load optimized expressions from JSON (works on Vercel) or SQLite (local dev)
DB_EXPRS = None
DB_AVAILABLE = False

# expressions.json  — flat JSON export, used in production (Vercel) and by default locally
# expressions.db    — full SQLite database, used locally when passed --db flag
USE_SQLITE = '--db' in sys.argv

def load_db():
    global DB_EXPRS, DB_AVAILABLE
    base = os.path.dirname(os.path.abspath(__file__))
    try:
        if USE_SQLITE:
            from core.db import get_conn
            conn = get_conn()
            rows = conn.execute('SELECT n, expr FROM numbers').fetchall()
            conn.close()
            DB_EXPRS = {str(r[0]): r[1] for r in rows}
        else:
            with open(os.path.join(base, 'expressions.json')) as f:
                raw = json.load(f)
            # support both old format {n: expr} and new format {n: {depth: expr, length: expr}}
            DB_EXPRS = {k: (v['depth'] if isinstance(v, dict) else v) for k, v in raw.items()}
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


MAX_CODE_LENGTH = 5000

@app.route('/api/code')
def api_code():
    code = request.args.get('code', '')
    if not code:
        return jsonify({'error': 'Missing code parameter'}), 400
    if len(code) > MAX_CODE_LENGTH:
        return jsonify({'error': f'Max {MAX_CODE_LENGTH} characters'}), 400
    raw_bytes = code.encode('utf-8')
    expr = compile_payload_stealth(code)
    return jsonify({'expr': expr, 'bytes': len(raw_bytes), 'len': len(expr)})


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


from core.strategies import STRATEGIES as ALL_STRATEGIES

# Only expose strategies with >1000 uses in the final DB
GRAPH_STRATEGY_NAMES = {
    'decrement', 'quad_plus_3', 'bytearray_4x', 'quint_plus_5',
    'list_range', 'triple', 'ascii_exp_2', 'dict_enum_bytes',
    'list_enum_bytes', 'zip_range', 'zip_chain_1', 'dict_enum_range',
    'ascii_exp_3', 'zip_chain_2', 'ascii_exp_4', 'zip_chain_3',
}
GRAPH_STRATEGIES = [(name, fns[0]) for name, fns in ALL_STRATEGIES.items() if name in GRAPH_STRATEGY_NAMES]
GRAPH_MAX = 200_000

def extract_path(inner_expr):
    """Walk the expression AST from innermost literal outward, recording each
    integer result. E.g. 'len(str(bytes(3)))' → [3, 15]."""
    import ast as _ast

    safe_env = {
        '__builtins__': {},
        'len': len, 'str': str, 'bytes': bytes, 'bytearray': bytearray,
        'list': list, 'range': range, 'max': max, 'ascii': ascii,
        'zip': zip, 'tuple': tuple, 'dict': dict, 'enumerate': enumerate,
    }

    try:
        tree = _ast.parse(inner_expr, mode='eval')
    except SyntaxError:
        return []

    path = []

    def walk(node):
        if isinstance(node, _ast.Constant) and isinstance(node.value, int):
            path.append(node.value)
            return
        if isinstance(node, _ast.Call) and node.args:
            walk(node.args[0])
            try:
                result = eval(_ast.unparse(node), safe_env)
                if isinstance(result, int):
                    path.append(result)
            except Exception:
                pass

    walk(tree.body)
    return path


@app.route('/api/neighbors/s')
def api_neighbors_s():
    neighbors = [{'id': str(n), 'strategy': 'anchor'} for n in sorted(BASE_ANCHORS)]
    return jsonify({'focus': 's', 'neighbors': neighbors})


@app.route('/api/path/<path:target>')
def api_path(target):
    if len(target) == 1 and not target.isdigit():
        n = ord(target)
    else:
        try:
            n = int(target)
        except ValueError:
            return jsonify({'error': 'Expected a single character or integer'}), 400

    if not DB_AVAILABLE or str(n) not in DB_EXPRS:
        return jsonify({'error': f'No path found for {repr(target)}'}), 404

    path = extract_path(DB_EXPRS[str(n)])
    if not path:
        return jsonify({'error': 'Could not extract path from expression'}), 500

    return jsonify({'target': n, 'path': path})


@app.route('/api/neighbors/<int:node_id>')
def api_neighbors(node_id):
    neighbors = []
    for strategy_name, forward_fn in GRAPH_STRATEGIES:
        try:
            target = forward_fn(node_id)
        except Exception:
            continue
        if isinstance(target, int) and 0 <= target <= GRAPH_MAX and target != node_id:
            neighbors.append({'id': target, 'strategy': strategy_name})
    return jsonify({'focus': node_id, 'neighbors': neighbors})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
