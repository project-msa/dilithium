import hashlib
import numpy as np
from polynomial import *

def expand_A(rho: bytes, k: int, l: int, n: int, q: int, root: int) -> PolyMatrix:
    """
    Generate A ∈ R_q^{k × l} using SHAKE128 as a stream of uniform coefficients mod q.
    """
    def rejection_sample(buffer, q, n):
        coeffs = []
        i = 0
        while len(coeffs) < n and i + 2 <= len(buffer):
            val = buffer[i] + (buffer[i+1] << 8)
            val &= 0x3FFF  # 14 bits
            if val < q:
                coeffs.append(val)
            i += 2
        return coeffs

    A = []
    for i in range(k):
        row = []
        for j in range(l):
            shake = hashlib.shake_128()
            shake.update(rho + bytes([i, j]))  # domain separation
            coeffs = []
            while len(coeffs) < n:
                buf = shake.digest(128)  # read 128 bytes
                coeffs += rejection_sample(buf, q, n - len(coeffs))
            poly = Poly(coeffs[:n], n, q, root)
            row.append(poly)
        A.append(row)

    return PolyMatrix(A)

def sample_small_polyvec(d: int, n: int, eta: int, q: int, root: int) -> PolyVec:
    """
    For sampling secret vectors s1 and s2 from S_eta^k and S_eta^l 
    """
    return PolyVec([
        Poly(np.random.randint(-eta, eta + 1, size=n), n, q, root) for _ in range(d)
    ])

def power2round(polyvec: PolyVec, d: int) -> tuple[PolyVec, PolyVec]:
    """
    Split polynomial into high and low parts: poly = high * 2^d + low
    """
    high, low = [], []
    for p in polyvec.polys:
        hi = (p.coeffs >> d) % p.q
        lo = (p.coeffs - (hi << d)) % p.q
        high.append(Poly(hi, p.n, p.q, p.root))
        low.append(Poly(lo, p.n, p.q, p.root))
    return PolyVec(high), PolyVec(low)