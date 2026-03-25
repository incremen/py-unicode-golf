"""
Payload compiler for py-unicode-golf.

Converts a raw Python script into a vars()-inception expression that extracts
exec from __builtins__ dynamically — the words eval/exec never appear in output.

Architecture:
  vars(vars().get(<"__builtins__">.decode())).get(<"exec">.decode())(<payload>)

Each string is encoded as bytes(next(zip(reversed(range(b+1)), ...)))
using the base-3 arithmetic pipeline.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.anchors import build_n


def _zip_ast(data: bytes) -> str:
    """Build bytes(next(zip(reversed(range(b+1)), ...))) for the given bytes."""
    parts = [f"reversed(range({build_n(b + 1)}))" for b in data]
    return f"bytes(next(zip({','.join(parts)})))"


def compile_payload(script: str) -> str:
    """exec(bytes(...)) — the word exec appears literally in the output."""
    payload_ast = _zip_ast(script.encode("utf-8"))
    return f"exec({payload_ast})"


def compile_payload_stealth(script: str) -> str:
    """vars()-inception — extracts exec from __builtins__, no exec/eval literals in output."""
    builtins_ast = _zip_ast(b"__builtins__")
    exec_ast     = _zip_ast(b"exec")
    payload_ast  = _zip_ast(script.encode("utf-8"))
    return (
        f"vars(vars().get({builtins_ast}.decode()))"
        f".get({exec_ast}.decode())"
        f"({payload_ast})"
    )


PAYLOAD_IMAGE = """\
import os, webbrowser
html = '<img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==">'
with open('img.html', 'w') as f:
    f.write(html)
webbrowser.open('file://' + os.path.realpath('img.html'))"""

PAYLOAD_GUI = """\
import tkinter as tk
root = tk.Tk()
root.title("py-unicode-golf")
tk.Label(root, text="Payload Executed.", font=("Helvetica", 24)).pack(padx=50, pady=50)
root.mainloop()"""

PAYLOAD_REDIRECT = """\
import webbrowser
webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')"""

PAYLOAD_CALCULATOR = """\
import tkinter as tk
root = tk.Tk()
root.title("Calculator")
expr = tk.StringVar()
tk.Entry(root, textvariable=expr, font=("Helvetica", 20), justify="right", bd=8).grid(row=0, column=0, columnspan=4)
def press(val):
    expr.set(expr.get() + val)
def clear():
    expr.set("")
def evaluate():
    try: expr.set(str(eval(expr.get())))
    except: expr.set("Error")
btns = ["7","8","9","/","4","5","6","*","1","2","3","-","0",".","=","+"]
for i,b in enumerate(btns):
    cmd = evaluate if b=="=" else lambda v=b: press(v)
    tk.Button(root, text=b, font=("Helvetica", 16), width=4, height=2, command=cmd).grid(row=1+i//4, column=i%4)
tk.Button(root, text="C", font=("Helvetica", 16), width=4, height=2, command=clear).grid(row=5, column=0, columnspan=4)
root.mainloop()"""

PAYLOADS = [
    ("payload_image.txt", PAYLOAD_IMAGE),
    ("payload_gui.txt", PAYLOAD_GUI),
    ("payload_redirect.txt", PAYLOAD_REDIRECT),
    ("payload_calculator.txt", PAYLOAD_CALCULATOR),
]

if __name__ == "__main__":
    for filename, script in PAYLOADS:
        print(f"Compiling {filename} ({len(script.encode('utf-8'))} bytes)...", end=" ", flush=True)
        expr = compile_payload_stealth(script)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(out_path, "w") as f:
            f.write(expr)
        print(f"done. ({len(expr):,} chars)")
    print("All payloads compiled.")
