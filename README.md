ai wrote this readme for now sorry i couldnt be bothered

# pyfuncs_to_chars

Write any character as a Python expression using **only builtin function calls** — no numeric literals, no string literals, no operators.
Each function must take in only one argument - pow(a,b) isn't allowed

## How it works

Everything starts from one trick:

```
not()  →  True
str(not())  →  "True"
min(str(not()))  →  "T"
ord(min(str(not())))  →  84
```

From 84, two operations let us reach other numbers:

- **Decrement**: `max(range(n))` = `n - 1` (2 parens per step)
- **Triangular jump**: `sum(range(k))` = `k * (k-1) / 2`

We also mine "anchors" — numbers we can construct cheaply from other builtins (e.g. `ord(max(str(bytes())))` = 98, because `str(bytes())` = `"b''"` and `max("b''"`) = `'b'`). To reach any target number, we find the nearest anchor above it and decrement down.

Finally, wrap in `chr()` to get the character.

## Usage

```
$ python3 write_char_as_pyfuncs.py
Enter a character: a

Expression for 'a' (code point 97):
chr(max(range(ord(max(str(bytes()))))))

Verify: eval gives 'a'
```

## Files

- `anchors.py` — base anchors, anchor expansion via triangular numbers, and `build_char()`
- `write_char_as_pyfuncs.py` — CLI wrapper
- `funcs_that_take_one_arg.txt` — exhaustive list of Python builtins that accept a single argument

## Constraints

- Python has a **200 nested parentheses limit**
- `chr()` wrapper costs 1 paren
- Each decrement (`max(range(...))`) costs **2 parens**
- Cheapest anchors cost 2-4 parens
- **Max ~98 decrements** per expression → anchors must be within ~98 of every target

## Coverage (current)

| Range | Coverage |
|---|---|
| 0-127 (ASCII) | 100% |
| 128-1000 | 100% |
| 1000-5000 | 99% |
| 5000-10000 | 79% |
| 10000-50000 | 40% |
| 50000-100000 | 23% |
| 100000-150000 | 18% |

Full ASCII works. Unicode coverage is ~30% of 0-150k.

## The bottleneck

`sum(range())` (triangular) is our only "growing" operation — it jumps quadratically. To cover 0-150k, we'd need every integer ~2 to ~548 reachable at low paren depth (since T(548) = 149,878). But reaching k=300 by decrementing from our highest base anchor (125) already blows the budget.

The core need: **cheap ways to produce numbers in the 100-550 range**, so their triangulars land densely across 0-150k.

## Open questions

- What single-arg builtin compositions can cheaply produce numbers in the 100-550 range?
- Are there other "growing" operations besides triangular that we're missing?
- Can chaining operations like `len(str(bytes(range(n))))` (~4n, linear growth) help fill gaps?
