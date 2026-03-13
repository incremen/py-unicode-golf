"""Tricks discovered during the string encoding research.

These don't directly help with single-character golf (which only uses
1-argument functions), but they're useful for the multi-argument string
pipeline and interesting in their own right.
"""


# ── O(1) Addition: slice().indices() ────────────────────────────────
#
# slice(A, B).indices(M) returns (A, B, 1) when M > A and M > B.
# Wrapping in sum() gives A + B + 1 instantly.
#
# sum(slice(A, B).indices(M)) = A + B + 1
#
# This is O(1) mathematical addition of two independent numbers
# using zero operators and zero dunders.
#
# For M, use a massive anchor like pow(125, 125) (262 digits).
# 125 = ord(max(str(dict()))) = ord('}')
#
# Example:
#   M = pow(125, 125)
#   sum(slice(64, 32).indices(M))  # = 64 + 32 + 1 = 97
#
# Limitation: each addition adds +1, so chaining K additions
# adds K to the total. Must account for this in the decomposition.


# ── O(1) Subtraction: len(range()) ──────────────────────────────────
#
# In Python 3, range objects calculate their length mathematically
# in C, without iterating.
#
# len(range(A, B)) = B - A  (for A <= B)
#
# This is O(1) subtraction. By nesting:
#   len(range(C, len(range(B, A)))) = (A - B) - C
#
# Useful for the "ceiling" approach: find pow(2, K) > N,
# then subtract down to N using binary decomposition of the difference.
#
# Limitation: len() can't return values > sys.maxsize (2^63).
# So this only works for numbers under ~9.2 quintillion.


# ── Ceiling Subtraction with pow() ──────────────────────────────────
#
# Instead of building N from 0 upward (base-3), start from a
# power-of-2 ceiling and subtract down.
#
# 1. Find K such that 2^K > N
# 2. Compute D = 2^K - N
# 3. Decompose D into binary: D = 2^b1 + 2^b2 + ... + R
# 4. Chain subtractions:
#    len(range(R, len(range(pow(2,b2), len(range(pow(2,b1), pow(2,K)))))))
#
# Each subtraction costs 12 chars (len(range(,))).
# pow(2, K) is built from the anchor for 2 + build_n(K).
#
# This produces shorter expressions than base-3 for very large numbers,
# but still hits the sys.maxsize wall at 2^63.


# ── The reversed(range()) Iterator Trick ────────────────────────────
#
# reversed(range(N)) yields N-1 as its first element.
# This creates a single-element-yielding iterator from a plain integer,
# which is exactly what zip() needs.
#
# zip(reversed(range(40)), reversed(range(113)))
# -> first element: (39, 112)
#
# next(zip(...)) extracts the tuple.
# bytes(...) converts to bytes.
# eval(...) parses the string literal.
#
# This avoids map(ord, ...) entirely - no uncalled function references.


# ── The zip() Tuple Packing Trick ───────────────────────────────────
#
# zip(iter1, iter2, ..., iterN) takes N iterables and produces
# tuples of their elements. With single-element iterators:
#
# next(zip(iter1, iter2, iter3)) = (first_of_1, first_of_2, first_of_3)
#
# This is the ONLY way to create a tuple of independent values
# using only builtin function calls (no [], no (), no literals).
#
# zip is the sole multi-argument exception in the string pipeline.
