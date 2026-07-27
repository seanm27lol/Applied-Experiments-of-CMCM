"""ops.py: operation systems for the cost-channel experiment.

Algebra: identical to Part IV's (fiber.py), which is the version with a
monotone ceiling structure. ONLY the rendering changes: the 28-bit state
is written as 7 hex digits, not 28 binary characters. That was Part IV's
fatal flaw, the model could not parse 28-character bit strings.

Under hex rendering the `readable` system becomes a literal copy task:
each push writes one hex digit, so after L=6 ops the last 6 hex digits
of the end state ARE the witness.

Costs are per-ACTION, distinct primes, summed along the path. The cost
scalar therefore reveals the operation multiset (up to collisions,
measured below) and carries no information about order.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "part_iv"))
import fiber as F

NBITS, MASK = F.NBITS, F.MASK
build = F.build_opset
START = 0x0BADC0DE & MASK
COSTS = [2, 3, 5, 7, 11, 13, 17, 19]

def render(s): return format(s, "08x")
def path_cost(seq): return sum(COSTS[k] for k in seq)
