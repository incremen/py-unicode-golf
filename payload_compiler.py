"""
Payload compiler for py-unicode-golf.

Converts a raw Python script into an exec(bytes(next(zip(...)))) expression
built entirely from zero-argument builtin function calls and base-3 arithmetic.
Writes output to .txt files (expressions are too large for the terminal).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.anchors import build_n


def compile_payload(script: str) -> str:
    """Encode script as UTF-8, then build the exec(bytes(next(zip(...)))) expression."""
    raw_bytes = script.encode("utf-8")
    rev_exprs = [f"reversed(range({build_n(b + 1)}))" for b in raw_bytes]
    return f'exec(bytes(next(zip({",".join(rev_exprs)}))))'


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
        expr = compile_payload(script)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(out_path, "w") as f:
            f.write(expr)
        print(f"done. ({len(expr):,} chars)")
    print("All payloads compiled.")
