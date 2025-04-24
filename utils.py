import hashlib
import numpy as np
from random import Random
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

def expand_mask(K: bytes, mu: bytes, nonce: int, l: int, n: int, gamma1: int, q: int, root: int) -> PolyVec:
    polys = []
    for i in range(l):
        shake = hashlib.shake_256()
        shake.update(K + mu + (nonce * l + i).to_bytes(2, 'little'))

        coeffs = []
        buf = b''
        buf_ptr = 0
        attempts = 0
        max_attempts = 100*n
        bound = (1 << 20) // (2 * gamma1 - 1) * (2 * gamma1 - 1)
        while len(coeffs) < n:
            print("trying")
            attempts += 1
            if attempts > max_attempts:
                raise RuntimeError("expand_mask : failed to sample enough coefficients")
            if buf_ptr + 5 > len(buf):
                buf += shake.digest(8192)  # buffer up front

            chunk = buf[buf_ptr:buf_ptr + 5]
            buf_ptr += 5
            t = int.from_bytes(chunk, 'little')
            v1 = t & 0xFFFFF
            v2 = (t >> 20) & 0xFFFFF

            for v in [v1, v2]:
                if v < bound:
                    print(v)
                    c = gamma1 - 1 - (v % (2*gamma1-1))
                    coeffs.append(c)
                    print("Adding coeff :",c%q)
                    if len(coeffs) == n:
                        break

        polys.append(Poly(coeffs, n, q, root))
    return PolyVec(polys)


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

def highbits_poly(p: Poly, alpha: int) -> Poly:
    hi = (p.coeffs // alpha) % p.q
    return Poly(hi, p.n, p.q, p.root)

def lowbits_poly(p: Poly, alpha: int) -> Poly:
    hi = (p.coeffs // alpha)
    lo = (p.coeffs - hi * alpha) % p.q
    return Poly(lo, p.n, p.q, p.root)

def highbits(pv: PolyVec, alpha: int) -> PolyVec:
    return PolyVec([highbits_poly(p, alpha) for p in pv.polys])

def lowbits(pv: PolyVec, alpha: int) -> PolyVec:
    return PolyVec([lowbits_poly(p, alpha) for p in pv.polys])

def generate_challenge(mu_w1_hash: bytes, n: int, q: int, root: int, tau: int = 60) -> Poly:
    """
    Generate a sparse ternary challenge polynomial with exactly `tau` ±1 coefficients, others zero.
    """
    if n < tau:
        tau = round(n*60/256)
    # SHAKE-256 XOF to generate deterministic randomness
    shake = hashlib.shake_256()
    shake.update(mu_w1_hash)
    buf = shake.digest(64 + tau)  # 64 for permutation seed, `tau` bytes for signs

    # Step 1: Generate a deterministic permutation of [0..n-1] using buffer as seed
    rng = Random(int.from_bytes(buf[:32], 'little'))  # deterministic seed
    perm = list(range(n))
    rng.shuffle(perm)

    # Step 2: Take first `tau` positions, assign ±1 signs from SHAKE buffer
    signs = buf[32:32 + tau]
    coeffs = np.zeros(n, dtype=int)

    for i in range(tau):
        sign = 1 if (signs[i] & 1) == 0 else -1
        coeffs[perm[i]] = sign

    return Poly(coeffs, n, q, root)

def decompose(r: np.ndarray, alpha: int, q: int) -> tuple[np.ndarray, np.ndarray]:
    r_modq = r % q
    r0 = ((r_modq + alpha // 2) % alpha) - (alpha // 2)
    r1 = ((r_modq - r0) // alpha) % q
    return r1, r0

def make_hint(c_t0: np.ndarray, w_sub_cs2_plus_ct0: np.ndarray, alpha: int, q: int) -> np.ndarray:
    r1, _ = decompose(w_sub_cs2_plus_ct0 - c_t0, alpha, q)
    v1, _ = decompose(w_sub_cs2_plus_ct0, alpha, q)
    return (r1 != v1).astype(np.uint8)  # 1 where hint needed

def make_hint_polyvec(c_t0: PolyVec, r: PolyVec, alpha: int) -> list[np.ndarray]:
    return [make_hint(ct.coeffs, rr.coeffs, alpha, ct.q) for ct, rr in zip(c_t0.polys, r.polys)]

def use_hint_polyvec(hint: list[np.ndarray], r: PolyVec, alpha: int) -> PolyVec:
    new_polys = []
    for p, h in zip(r.polys, hint):
        r_modq = p.coeffs % p.q
        r0 = ((r_modq + alpha // 2) % alpha) - (alpha // 2)
        r1 = ((r_modq - r0) // alpha) % p.q

        # Apply hint: if hint[i] == 1, replace r1[i] with (r1[i] + 1) % q
        r1 = (r1 + h) % p.q
        new_polys.append(Poly(r1, p.n, p.q, p.root))
    return PolyVec(new_polys)