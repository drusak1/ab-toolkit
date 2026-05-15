"""Deterministic user → bucket → group split using salted hash."""
from __future__ import annotations

import hashlib
import secrets

import numpy as np
import pandas as pd


def generate_salt(n: int = 7) -> str:
    return secrets.token_urlsafe(n)[:n]


def _hash_to_bucket(uid: str, salt: str, n_buckets: int) -> int:
    h = hashlib.md5(f"{uid}{salt}".encode()).hexdigest()
    return int(h, 16) % n_buckets


def assign_groups(user_ids: pd.Series | np.ndarray, salt: str, n_buckets: int) -> np.ndarray:
    """Assigns each user to bucket [0, n_buckets). Even buckets → group A, odd → group B."""
    ids = pd.Series(user_ids).astype(str)
    buckets = ids.apply(lambda u: _hash_to_bucket(u, salt, n_buckets)).to_numpy()
    return buckets


def buckets_to_ab(buckets: np.ndarray) -> np.ndarray:
    """0 = control (A), 1 = treatment (B). Splits buckets in half."""
    n = buckets.max() + 1
    half = n // 2
    return (buckets >= half).astype(int)
