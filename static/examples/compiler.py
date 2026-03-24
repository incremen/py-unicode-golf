ONE = 'int(not())'

def build_n(n):
    if n == 1: return ONE
    q = -(-n // 3)
    r = 3 * q - n
    expr = f'len(str(list(bytes({build_n(q)}))))'
    for _ in range(r):
        expr = f'max(range({expr}))'
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
