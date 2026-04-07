# py-unicode-golf

(more of a challenge than anything. this isn't useful)

Represent any character using only Python builtin function calls that take up to one argument, in one line.

For example: `chr(sum(range(ord(min(str(not())))))) = ඞ`

I found an algorithm to represent each character this way - it works kind of like base 3 representation.
To find the shortest representation we can for each character, we run optimizations (using Dijkstra! yay) to find the shortest path/expression for each character -
for example, the algorithm represents "ڐ" as `chr(len(str(list(bytes(max(range(len(str(list(bytes(max(range(max(range(len(str(list(bytes(len(str(list(bytes(len(str(type(classmethod(int())))))))))))))))))))))))))))`.
But the optimized database has this representation: `chr(len(str(dict(enumerate(range(sum(range(len(str(type(ValueError())))))))))))`.


The project also handles arbitrary strings (using `zip` with multiple arguments) and can compile entire Python scripts into one really long composition of functions - without using `exec`.

Details in:

**Website:** https://py-unicode-golf.vercel.app

If you understand how the optimization works and are curious about how the underlying graph looks, check out:
https://py-unicode-golf.vercel.app/static/graph/graph.html - uses Cyptoscape.js for showing graphs in a way that i think is pretty cool.


Uses Flask for server stuff and SQLite for db.

### Local development

```bash
pip install -e .
python app.py
```

---

## Project structure

- `core/` - core logic
  - `config.py` - shared constants (`MAX_N`, `STORE_N`)
  - `anchors.py` - base anchor generation from zero-arg builtins
  - `builder.py` - expression builder (`build_n`, `build_char`, `build_string`)
  - `strategies.py` - Dijkstra strategies (forward functions + expression templates)
  - `db.py` - SQLite database for optimized expressions
  - `compile.py` - payload compilation (arbitrary Python code → builtins-only)
  - `visualize.py` - step-by-step expression evaluator
- `scripts/` - CLI tools
  - `optimize_dijksta.py` - Dijkstra optimizer (builds 0..MAX_N graph, merges best into DB)
  - `optimize_iterative.py` - iterative DP optimizer (improves DB using inverse functions)
  - `verify_db.py` - verify all DB expressions evaluate correctly
  - `export_stats.py` - export DB stats to static JS files
  - `benchmark.py` - compute performance stats
  - `test_strategy.py` - test new strategies without writing to DB
- `static/` - frontend
  - `js/` - main page JS (visualizer, panels, logo animation, prefetch)
  - `graph/` - interactive graph explorer (Cytoscape.js)
  - `css/`, `data/`, `img/`, `examples/`
- `app.py` - Flask web app + API endpoints
- `expressions.json` - pre-optimized expressions for Vercel deployment
- `expressions.db` - SQLite database (local dev only, not tracked in git)

---

## API (if you need that for some reason):

### `GET /api/expr/<char>` or `GET /api/expr?c=<char>`

Returns just the expression as plain text (no JSON). Uses the optimized db expression if available, otherwise falls back to the formula.
for example:

```
curl https://py-unicode-golf.vercel.app/api/expr/A
```

returns

```
chr(len(ascii(str(bytes(max(range(len(str(type(int()))))))))))
```

### `GET /api/char/<char>` or `GET /api/char?c=<char>`

will return json data.
For example:

```
curl https://py-unicode-golf.vercel.app/api/char/A
```

returns

```json
{"char":"A",
"code_point":65,
"name":"LATIN CAPITAL LETTER A",
"db":{"depth":11,"expr":"chr(len(ascii(str(bytes(max(range(len(str(type(int()))))))))))", "len":62},
"formula":{"depth":12,"expr":"chr(max(range(len(str(list(bytes(len(str(type(iter(set())))))))))))) ","len":67}}
```

`formula` is generated on-the-fly. `db` (if present) is the pre-optimized expression from the database.

### `GET /api/string?s=<text>`

Returns the expression for an arbitrary string (up to 200 characters). Uses `zip` with multiple arguments.

```
curl https://py-unicode-golf.vercel.app/api/string?s=hi
```

returns

```json
{"text":"hi",
"expr":"eval(bytes(next(zip(reversed(range(...)),reversed(range(...)),...))))",
"depth":57,
"len":319}
```

### `GET /api/code?code=<python_code>`

Compiles an entire Python script into a builtins-only expression using `exec`.

```
curl 'https://py-unicode-golf.vercel.app/api/code?code=print("hi")'
```

returns

```json
{"expr":"exec(bytes(next(zip(...))))","bytes":10,"len":1234}
```

---

## Contributing

If you found a new anchor or strategy, please [Open an issue](https://github.com/incremen/py-unicode-golf/issues/new/choose). I'll test it and see if I can improve the database.
