from core.strategies import _DIGIT_SUM
import random
random.seed(42)
MAX = 500
samples = random.sample(range(0, 500_001), MAX)
errors = 0
for n in samples:
    if n == 0:
        el, ed = 2, 2
    else:
        el = _DIGIT_SUM[n] + 7 * n
        ed = _DIGIT_SUM[n] + 5 * n
    actual_list = len(str(list(enumerate(bytes(n)))))
    actual_dict = len(str(dict(enumerate(bytes(n)))))
    if actual_list != el or actual_dict != ed:
        print(f'n={n}: list actual={actual_list} formula={el} | dict actual={actual_dict} formula={ed}')
        errors += 1
print(f'errors: {errors} / {MAX}')
