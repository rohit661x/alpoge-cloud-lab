"""Exact switch-floor schedules for centered 3x3 BFV row rotations."""
from collections import deque
from itertools import combinations
from pathlib import Path
import json

ROW = 4096
PITCH = 64
TARGET = {x + y * PITCH for x in (-1, 0, 1) for y in (-1, 0, 1)}
LABELS = sorted({v - u for v in TARGET for u in TARGET if v != u})


def shortest_tree(keys):
    depth = {0: 0}
    queue = deque([0])
    edges = []
    while queue:
        u = queue.popleft()
        for k in keys:
            v = u + k
            if v in TARGET and v not in depth:
                depth[v] = depth[u] + 1
                queue.append(v)
                edges.append([u, k, v])
    if len(depth) == len(TARGET):
        return max(depth.values()), edges


def check(keys, edges, claimed_depth):
    # Replay using actual residues. Independently verify each new materialization.
    expected = {v % ROW for v in TARGET}
    levels = {0: 0}
    for parent, step, child in edges:
        start, end = parent % ROW, child % ROW
        assert start in levels and end in expected and end not in levels
        assert step in keys and (start + step) % ROW == end
        levels[end] = levels[start] + 1
    assert set(levels) == expected and max(levels.values()) == claimed_depth
    assert len(edges) == 8


def main():
    assert len(LABELS) == len({k % ROW for k in LABELS}) == 24
    assert len({(x + PITCH*y) % ROW for x in range(-2, 3)
                for y in range(-2, 3)}) == 25
    witnesses = {}
    for count in range(1, 5):
        best = None
        tried = 0
        for keys in combinations(LABELS, count):
            tried += 1
            result = shortest_tree(keys)
            if result is None:
                continue
            depth, edges = result
            if best is None or depth < best['minimum_depth']:
                check(keys, edges, depth)
                best = dict(keys=list(keys), minimum_depth=depth, edges=edges)
        witnesses[count] = (best, tried)
    assert [witnesses[i][0] is None for i in (1, 2)] == [True, True]
    assert [witnesses[i][0]['minimum_depth'] for i in (3, 4)] == [3, 2]

    # For budgets 5..7 the four-key witness reaches the depth-two bound.
    # Depth one needs eight different nonzero first moves. Verify the direct plan.
    direct = sorted(TARGET - {0})
    depth, edges = shortest_tree(direct)
    check(direct, edges, 1)
    certificate = dict(row_length=ROW, pitch=PITCH, targets=sorted(TARGET),
                       useful_directions=LABELS, edge_fields=['parent', 'step', 'child'],
                       search_counts={k: v[1] for k, v in witnesses.items()},
                       budgets={})
    for budget in range(9):
        if budget == 8:
            plan = dict(keys=direct, minimum_depth=depth, edges=edges)
        elif budget >= 4:
            plan = witnesses[4][0]
        else:
            plan = witnesses.get(budget, (None, 0))[0]
        certificate['budgets'][budget] = plan
    output = Path(__file__).with_name('certificate.json')
    output.write_text(json.dumps(certificate, indent=2) + '\n')
    print('Verified budgets 0..8; minimum depths: infeasible x3, 3, 2, 2, 2, 2, 1.')


if __name__ == '__main__':
    main()
