# py-unicode-golf

(more of a challenge than anything. this isn't useful)

Represent any character using only Python builtin function calls that take up to one argument, in one line.

For example: `chr(sum(range(ord(min(str(not())))))) = ඞ`

I found a closed algorithm to represent each character this way. Also, there's a database that stores optimized representations.
Also I do this with strings too, but allow multiple arguments.

Details in:

**Website:** https://py-unicode-golf.vercel.app

Uses Flask for server stuff and SQLite for db.
---

## Project structure

- `core/` - the algorithm: base-3 number builder, optimization strategies, step-by-step evaluator
- `scripts/` - CLI tools for optimizing the database and exporting stats
- `reference/` - documentation of all known strategies
- `static/` - frontend: HTML, CSS, JS (split into utils, logo animation, visualizer, prefetch, panels)
- `static/data/` - generated stats files (optimization history, strategy breakdown, unicode ranges)
- `app.py` - Flask web app + API endpoints
- `expressions.db` / `expressions.json` - the optimized expression database (SQLite for local dev, JSON for Vercel)

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

---

## Contributing

If you found a new anchor or strategy, please [Open an issue](https://github.com/incremen/py-unicode-golf/issues/new/choose). I'll test it and see if I can improve the database.
