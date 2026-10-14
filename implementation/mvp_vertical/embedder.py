"""Deterministic local embedder (feature hashing).

Deliberate placeholder: retrieval *quality* is not Block 1's subject — the
scope boundary is. This embedder is pure stdlib, deterministic, offline
(zero data exposure), and swappable for a real model behind the same
function signature. Swapping it is a reviewed decision, because it is the
data-exposure decision.
"""

from __future__ import annotations

import hashlib
import math
import re

DIM = 256
_TOKEN = re.compile(r"[a-zà-ÿ0-9]{2,}", re.IGNORECASE)

# Function words carry no perimeter signal and create false similarity
# between unrelated texts; they are dropped before hashing.
_STOPWORDS = frozenset("""
au aux avec ce ces cette dans de des du elle en et est il ils je la le les
leur lui ma mais me même mes moi mon ne nos notre nous on ou où par pas pour
qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous y
d l n s t qu' d' l' est-il correspond-il
the a an and or of to in on for is are be with without this that it its as
""".split())


def embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for token in _TOKEN.findall(text.lower()):
        if token in _STOPWORDS:
            continue
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[index] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
