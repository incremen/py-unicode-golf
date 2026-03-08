"""Flask web app for py-unicode-golf"""

import os
import json
from urllib.parse import unquote
from flask import Flask, jsonify, send_from_directory, request
from anchors import build_n, build_char, BASE_ANCHORS

app = Flask(__name__, static_folder='static')

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
            from db import get_conn
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
        from db import get_log
        return jsonify(get_log())
    return jsonify([])


stats_cache = None

def compute_stats():
    global stats_cache
    if not DB_AVAILABLE:
        stats_cache = {'total': 0, 'avg_depth': 0, 'max_depth': 0, 'avg_len': 0, 'max_len': 0}
    else:
        exprs = list(DB_EXPRS.values())
        depths = [e.count('(') for e in exprs]
        lengths = [len(e) for e in exprs]
        stats_cache = {
            'total': len(exprs),
            'avg_depth': round(sum(depths) / len(depths), 2),
            'max_depth': max(depths),
            'avg_len': round(sum(lengths) / len(lengths), 1),
            'max_len': max(lengths),
        }

compute_stats()

@app.route('/api/stats')
def api_stats():
    return jsonify(stats_cache)


formula_stats_cache = None

def compute_formula_stats():
    global formula_stats_cache
    sample = list(range(0, 200_001, 10))
    depths = []
    lengths = []
    for n in sample:
        expr = f'chr({build_n(n)})'
        depths.append(expr.count('('))
        lengths.append(len(expr))
    formula_stats_cache = {
        'sample_size': len(sample),
        'avg_depth': round(sum(depths) / len(depths), 1),
        'max_depth': max(depths),
        'avg_len': round(sum(lengths) / len(lengths), 1),
        'max_len': max(lengths),
    }

compute_formula_stats()

@app.route('/api/formula-stats')
def api_formula_stats():
    return jsonify(formula_stats_cache)


@app.route('/api/anchors')
def api_anchors():
    return jsonify({str(k): v for k, v in sorted(BASE_ANCHORS.items())})


import re

VISUALIZE_PATTERN = re.compile(r'\b([a-z_]+)\(([^()]*)\)')


@app.route('/api/visualize')
def api_visualize():
    expr = request.args.get('expr', '')
    if not expr:
        return jsonify({'error': 'Missing expr parameter'}), 400

    steps = []
    current = expr
    # Track substituted values so we can eval with them in scope
    placeholders = {}
    counter = [0]

    def make_placeholder(value):
        name = f'_v{counter[0]}'
        counter[0] += 1
        placeholders[name] = value
        return name

    for _ in range(200):
        match = VISUALIZE_PATTERN.search(current)
        if not match:
            break

        func_call = match.group(0)

        # Build display version (substitute placeholders back to repr)
        display = current
        for name, val in placeholders.items():
            display = display.replace(name, repr(val))

        try:
            result = eval(func_call, {"__builtins__": __builtins__}, placeholders)
            result_repr = repr(result)

            pre = current[:match.start()]
            for name, val in placeholders.items():
                pre = pre.replace(name, repr(val))
            d_start = len(pre)
            call_display = func_call
            for name, val in placeholders.items():
                call_display = call_display.replace(name, repr(val))
            d_end = d_start + len(call_display)

            steps.append({
                'expr': display,
                'highlight': {'start': d_start, 'end': d_end},
                'call': call_display,
                'result': result_repr
            })

            # Use placeholder if repr contains parens (would confuse regex)
            if '(' in result_repr or ')' in result_repr:
                placeholder = make_placeholder(result)
                current = current[:match.start()] + placeholder + current[match.end():]
            else:
                current = current[:match.start()] + result_repr + current[match.end():]

        except Exception as e:
            display_call = func_call
            for name, val in placeholders.items():
                display_call = display_call.replace(name, repr(val))
            steps.append({
                'expr': display,
                'call': display_call,
                'error': str(e)
            })
            break

    # Final display
    final = current
    for name, val in placeholders.items():
        final = final.replace(name, repr(val))
    steps.append({'expr': final, 'final': True})

    return jsonify({'steps': steps})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
