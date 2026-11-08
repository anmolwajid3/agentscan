"""Cohen's kappa and linear weighted kappa.

0 means the two raters agree only as often as chance. 1 means they agree
on every case. The pilot passes at 0.6 or higher for decision type and for
the yes/no hard dimension.
"""

from __future__ import annotations

from collections import Counter


def cohens_kappa(pairs: list[tuple[str, str]]) -> dict:
    """Unweighted Cohen's kappa for categorical labels."""
    if not pairs:
        return {"n": 0, "kappa": None, "observed": None, "expected": None, "labels": []}
    labels = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    index = {label: i for i, label in enumerate(labels)}
    size = len(labels)
    matrix = [[0 for _ in labels] for _ in labels]
    for left, right in pairs:
        matrix[index[left]][index[right]] += 1
    n = len(pairs)
    observed = sum(matrix[i][i] for i in range(size)) / n
    row = [sum(matrix[i][j] for j in range(size)) for i in range(size)]
    col = [sum(matrix[i][j] for i in range(size)) for j in range(size)]
    expected = sum(row[i] * col[i] for i in range(size)) / (n * n)
    if abs(expected - 1) < 1e-12:
        kappa = 1.0 if observed == 1 else 0.0
    else:
        kappa = (observed - expected) / (1 - expected)
    return {
        "n": n,
        "kappa": kappa,
        "observed": observed,
        "expected": expected,
        "labels": labels,
        "matrix": matrix,
    }


def weighted_kappa(pairs: list[tuple[int, int]], categories: list[int] | None = None) -> dict:
    """Linear weighted kappa for ordered scores such as 0, 1, 2."""
    if not pairs:
        return {"n": 0, "kappa": None}
    cats = categories or sorted({a for a, _ in pairs} | {b for _, b in pairs})
    index = {cat: i for i, cat in enumerate(cats)}
    size = len(cats)
    matrix = [[0 for _ in cats] for _ in cats]
    for left, right in pairs:
        matrix[index[left]][index[right]] += 1
    n = len(pairs)
    row = [sum(matrix[i][j] for j in range(size)) for i in range(size)]
    col = [sum(matrix[i][j] for i in range(size)) for j in range(size)]
    expected = [[(row[i] * col[j]) / n for j in range(size)] for i in range(size)]
    denom = size - 1 or 1

    def weight(i: int, j: int) -> float:
        return abs(i - j) / denom

    observed_disagreement = sum(weight(i, j) * matrix[i][j] for i in range(size) for j in range(size)) / n
    expected_disagreement = sum(weight(i, j) * expected[i][j] for i in range(size) for j in range(size)) / n
    if expected_disagreement == 0:
        kappa = 1.0 if observed_disagreement == 0 else 0.0
    else:
        kappa = 1 - observed_disagreement / expected_disagreement
    return {
        "n": n,
        "kappa": kappa,
        "observed_disagreement": observed_disagreement,
        "expected_disagreement": expected_disagreement,
        "categories": cats,
    }


def confusion(pairs: list[tuple[str, str]]) -> Counter:
    return Counter(pairs)
