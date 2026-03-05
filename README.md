# py-unicode-golf

Represent any character using only Python builtin function calls that take up to one argument.

For example: `chr(sum(range(ord(min(str(not())))))) = ඞ`

**Website:** https://py-unicode-golf.vercel.app

Uses Flask for server stuff and SQLite for db.
Used Claude Opus for basically the entire frontend, I really couldn't be bothered with html.

## API (if you need that for some reason):

### `GET /api/char/<char>` or `GET /api/char?c=<char>`
will return json data.
For example:
```
curl https://py-unicode-golf.vercel.app/api/char/A
```
will return the json:
```json
{"char":"A",
"code_point":65,
"db":{"depth":11,"expr":"chr(len(ascii(str(bytes(max(range(len(str(type(int()))))))))))","len":62},
"formula":{"depth":12,"expr":"chr(max(range(len(str(list(bytes(len(str(type(iter(set())))))))))))","len":67}}
```

`formula` is generated on-the-fly. `db` (if present) is the pre-optimized expression from the database.
