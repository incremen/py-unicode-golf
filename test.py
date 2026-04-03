import os
import json
path = os.path.join(os.path.dirname(__file__), 'expressions.json')

vals = json.load(open(path))
print(f"{len(vals)} expressions loaded from {path}")
print("Sample:", {k: vals[k] for k in sorted(vals)[:10]})