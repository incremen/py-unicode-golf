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
root.mainloop()
