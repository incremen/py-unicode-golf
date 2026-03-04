# pyfuncs_to_chars

Represent any character using only Python builtin function calls. No numeric literals, no string literals, no operators. Each function takes exactly one argument.

## Why?

Right around the whole Among Us time, it was gaining traction that `chr(sum(range(ord(min(str(not()))))))` in Python evaluates to "ඞ". I immediately tried to generalize it. Could any Unicode character (~160,000) be represented like this?

The rules:
- The final function must take in no parameters, like `not()`.
- Each function can only take in one parameter; `pow(a,b)` isn't allowed.
- Represent each Unicode character as a composition of these functions.

Since we only aim to find the Unicode value of the character and then apply `chr()` to it, the struggle is essentially to find a neat representation for each number 1–160,000. And the representation MUST be neat, since Python won't let you have more than 200 nested parentheses.

## The formula

Two operations are enough to build any number:

**Subtract 1:** `max(range(n))` returns n - 1. Costs 2 parentheses.

**Multiply by 3:** `len(str(list(bytes(n))))` returns exactly 3n. bytes(n) creates n zero-bytes, list() turns it into [0, 0, ..., 0], str() gives "[0, 0, ..., 0]" — always exactly 3n characters. Costs 4 parentheses.

**The algorithm:** decompose n in base 3. At each step, build ceil(n/3), triple it, then subtract the remainder (0, 1, or 2). Stop when you reach a base anchor — a small number you can construct directly. The only base anchors you actually need are `1 = int(not())` and `0 = int(not(not()))`.

```
function build(n):
    if n is a base anchor:
        return the anchor expression

    q = ceil(n / 3)
    r = 3 * q - n              // r is 0, 1, or 2

    expr = triple(build(q))    // multiply by 3
    expr = subtract(expr, r)   // subtract 0, 1, or 2
    return expr
```

**Example: build(13)**

13 = 15-2 = 5\*3-2 = (3\*2-1)\*3-2

```
build(13):  q = ceil(13/3) = 5,  r = 2  →  13 = triple(build(5)) - 2
build(5):   q = ceil(5/3) = 2,   r = 1  →   5 = triple(build(2)) - 1
build(2):   base anchor  →  len(str(ord(min(str(not())))))
```

## Optimizations

The base-3 formula works for everything but isn't always the shortest. The optimizer tries all of these on every number and keeps the best.

**Exact multipliers** — stringifying bytes objects in different ways:

| Expression | Formula | Parens |
|---|---|---|
| `len(str(list(bytes(n))))` | 3n | 4 |
| `len(str(bytes(n)))` | 4n + 3 | 3 |
| `len(ascii(str(bytes(n))))` | 5n + 5 | 4 |

**Zip chain** — each zip() wrapper adds 3n to the string length:

| Expression | Formula | Parens |
|---|---|---|
| `len(str(list(zip(bytes(n)))))` | 6n | 5 |
| `len(str(list(zip(zip(bytes(n))))))` | 9n | 6 |
| ...k zips... | 3(k+1)n | 4+k |

**Ascii exponential** — `ascii()` escapes backslashes, doubling them each time. `f(n) = (2^k + 3)n + (2^(k+1) + 1)`:

| k | Formula | Parens |
|---|---|---|
| 1 | 5n + 5 | 4 |
| 2 | 7n + 9 | 5 |
| 3 | 11n + 17 | 6 |
| 4 | 19n + 33 | 7 |
| 5 | 35n + 65 | 8 |
| 6 | 67n + 129 | 9 |
| 10 | 1027n + 2049 | 13 |

**Triangular jump** — `sum(range(n))` = n(n-1)/2. Quadratic growth, 2 parens.

## Database

The database stores the shortest known expression for each number from 0 to 200,000. Each entry records which strategy produced it and which smaller number it depends on.

| Stage | Avg depth | Max depth | Avg length |
|---|---|---|---|
| minimal formula (seeds: 0, 1) | 66.6 | 93 | 386 |
| full formula (44 base anchors) | 55.5 | 102 | 322 |
| optimizer (offset ≤ 2) | 22.4 | 35 | 131 |
| deep search (offset ≤ 10) | 22.3 | 32 | 131 |


