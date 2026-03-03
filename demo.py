constructible = {}

constructible[84] = 'ord(min(str(not())))'

for n in reversed(range(1, 84)):
    print(f"{n=}")
    inner = constructible[n+1]
    to_eval = f"next(reversed(range({inner})))"
    print(f"eval({to_eval})={eval(to_eval)}")
    with open ('output.txt', 'a') as f:
        f.write(f"eval({to_eval})={eval(to_eval)}\n")
    constructible[n] = to_eval      