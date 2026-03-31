# Claude Code Instructions

## Code structure

- All logic must live inside functions. Scripts that are meant to be run directly must call a `main()` function at the bottom under `if __name__ == '__main__'`.
- Functions should be short and focused. If a function is getting long, split it. Exceptions: specific algorithms (Dijkstra loops, etc.) or cases where extracting sub-functions would genuinely make the code harder to follow.
- Don't over-engineer. If a helper would only ever be called once and makes the caller harder to read, just inline it.

## Naming

- No single-letter variable names. Exception: `i`, `j`, `k` in tight loops where the meaning is obvious from context.
- Variable and function names must be descriptive. A reader should understand what something holds/does without reading its implementation.
- Don't prefix things with `_` unless there is a real reason (e.g. a method that genuinely should not be called from outside a class). `for _i in range(...)` is nonsense — just call it `i` or give it a real name.
- Don't make functions private (`_name`) unless there is a strong reason. Default to public.

## Style

- Prefer clarity over brevity. Don't compress logic into one-liners just because Python allows it.
- Avoid redundant comments. Don't comment what the code already says clearly. Do comment *why* something non-obvious is done.
- Consistent formatting: spaces around operators, blank lines between logical sections of a function.

## Python specifics

- Avoid mutable default arguments (`def f(x=[])`).
- Prefer f-strings over `.format()` or `%`.
- Use `get()` on dicts when the key might be absent rather than `try/except KeyError`.
- Don't shadow built-ins (`list`, `type`, `input`, `id`, etc.).
- Keep imports at the top of the file. No inline imports except for optional heavy dependencies or circular import workarounds.

## What not to do

- Don't add features or refactor things that weren't asked for.
- Don't add error handling for cases that can't realistically happen.
- Don't add docstrings to functions whose name and signature already explain them.
- Don't over-abstract. Three similar lines of code is fine. A factory-factory is not.
- Don't use abbreviations in names unless they are universally understood (`url`, `db`, `id`, `n` for a math variable).
