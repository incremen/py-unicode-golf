import sys

ANCHORS = {
    0:   'int(not(not()))',
    1:   'int(not())',
    2:   'len(str(ord(min(str(not())))))',
    3:   'len(bin(int(not())))',
    4:   'len(str(not()))',
    5:   'len(bin(len(str(not()))))',
    6:   'sum(range(len(str(not()))))',
    11:  'len(str(frozenset()))',
    13:  'len(str(type(int())))',
    14:  'len(str(type(not())))',
    15:  'len(str(type(float())))',
    17:  'len(str(type(complex())))',
    18:  'len(str(type(property())))',
    19:  'len(str(type(frozenset())))',
    20:  'len(str(type(memoryview(bytes()))))',
    21:  'len(str(type(classmethod(int()))))',
    22:  'len(str(type(iter(set()))))',
    23:  'len(str(type(iter(list()))))',
    24:  'len(str(type(iter(bytes()))))',
    26:  'len(str(type(iter(dict()))))',
    28:  'len(str(type(iter(str()))))',
    30:  'len(str(type(reversed(list()))))',
    33:  'len(str(type(reversed(dict()))))',
    32:  'ord(min(str(type(not()))))',
    39:  'ord(min(str(bytes())))',
    40:  'ord(min(str(tuple())))',
    41:  'ord(max(str(tuple())))',
    46:  'ord(min(str(float())))',
    48:  'ord(max(str(float())))',
    70:  'ord(min(str(not(not()))))',
    84:  'ord(min(str(not())))',
    91:  'ord(min(str(list())))',
    93:  'ord(max(str(list())))',
    98:  'ord(max(str(bytes())))',
    106: 'ord(max(str(complex())))',
    111: 'ord(max(oct(int(not()))))',
    115: 'ord(max(str(not(not()))))',
    116: 'ord(max(str(set())))',
    117: 'ord(max(str(not())))',
    120: 'ord(max(hex(int(not()))))',
    121: 'ord(max(str(type(type(not())))))',
    122: 'ord(max(str(frozenset())))',
    123: 'ord(min(str(dict())))',
    125: 'ord(max(str(dict())))',
}

memo = {}

def build_n(n):
    if n in memo: return memo[n]
    if n in ANCHORS: memo[n] = ANCHORS[n]; return memo[n]
    q = -(-n // 3)
    r = 3 * q - n
    expr = f'len(str(list(bytes({build_n(q)}))))'
    for _ in range(r):
        expr = f'max(range({expr}))'
    memo[n] = expr
    return expr

print("enter script line by line, type END to compile:")
lines = []
while True:
    line = input("... " if lines else ">>> ")
    if line == "END":
        break
    lines.append(line)
src = "\n".join(lines).encode()

parts = [f'reversed(range({build_n(b + 1)}))' for b in src]
print(f'exec(bytes(next(zip({",".join(parts)}))))')
