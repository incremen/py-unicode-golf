from core.build_base_3 import build_n


def _zip_ast(data: bytes) -> str:
    parts = [f'reversed(range({build_n(b + 1)}))' for b in data]
    return f'bytes(next(zip({",".join(parts)})))'


def compile_payload(script: str) -> str:
    """exec(bytes(...)) — the word exec appears literally in the output."""
    return f'exec({_zip_ast(script.encode("utf-8"))})'


def compile_payload_stealth(script: str) -> str:
    """vars()-inception — extracts exec from __builtins__, no exec/eval literals in output."""
    return (
        f'vars(vars().get({_zip_ast(b"__builtins__")}.decode()))'
        f'.get({_zip_ast(b"exec")}.decode())'
        f'({_zip_ast(script.encode("utf-8"))})'
    )
