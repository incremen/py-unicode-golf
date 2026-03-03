# pyfuncs_to_chars

Write any character as a Python expression using **only builtin function calls** — no numeric literals, no string literals, no operators.

## How it works

Everything starts from one trick:

```
not()  →  True
str(not())  →  "True"
min(str(not()))  →  "T"
ord(min(str(not())))  →  84
```

From 84, two operations let us reach other numbers:

- **Decrement**: `next(reversed(range(n)))` = `n - 1`
- **Triangular jump**: `sum(range(k))` = `k * (k-1) / 2`

We also mine "anchors" — numbers we can construct cheaply from other builtins (e.g. `ord(max(str(bytes())))` = 98, because `str(bytes())` = `"b''"` and `max("b''"`) = `'b'`). To reach any target number, we find the nearest anchor above it and decrement down.

Finally, wrap in `chr()` to get the character.

## Usage

```
$ python3 write_char_as_pyfuncs.py
Enter a character: a

Expression for 'a' (code point 97):
chr(next(reversed(range(ord(max(str(bytes())))))))

Verify: eval gives 'a'
```

## Files

- `anchors.py` — base anchors, anchor expansion via triangular numbers, and `build_char()`
- `write_char_as_pyfuncs.py` — CLI wrapper
- `funcs_that_take_one_arg.txt` — exhaustive list of Python builtins that accept a single argument

## Problems and goals

### Python has a 200-paren nesting limit

Each decrement (`next(reversed(range(...)))`) costs 3 parentheses. With `chr()` taking 1, and the cheapest anchors costing 2-4, we can afford **~65 decrements** before hitting the limit. That means every target code point must have an anchor within 65 of it.

### ASCII is covered, Unicode is not

The current anchor set (32 base + ~30 expanded via triangular numbers = 62 total) covers ASCII fine. But Unicode has ~150,000 characters. We'd need roughly **one anchor per 65 code points**, or ~2,300 anchors, to cover all of Unicode.

The triangular expansion helps but creates sparse, exponentially growing jumps (84 → 3486 → 6,078,705) with huge gaps in between.

### We need more operations

Right now we only go *down* (decrement) and *up* (triangular jump). To fill the gaps densely, we probably need:

- More ways to combine existing numbers (multiplication? exponentiation via `pow()`?)
- More base anchors mined from unexplored builtins
- Possibly chaining operations in new ways (e.g. `sum(range(sum(range(k))))` for nested triangulars)

### Open questions

- What's the most efficient set of operations to cover the full Unicode range within the 200-paren budget?
- Can we find builtins that produce useful intermediate values we haven't discovered yet?
- Is there a smarter search strategy than "nearest anchor above + decrement"?
