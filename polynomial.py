import numpy as np
from typing import List, Tuple

# --------------------
# NTT and Helpers
# --------------------

def bit_reverse(x: int, bits: int) -> int:
    result = 0
    for i in range(bits):
        if x & (1 << i):
            result |= 1 << (bits - 1 - i)
    return result

def bit_reverse_array(a: np.ndarray) -> np.ndarray:
    n = len(a)
    bits = n.bit_length() - 1
    return np.array([a[bit_reverse(i, bits)] for i in range(n)], dtype=int)

def modinv(a: int, q: int) -> int:
    t, newt = 0, 1
    r, newr = q, a
    while newr != 0:
        quotient = r // newr
        t, newt = newt, t - quotient * newt
        r, newr = newr, r - quotient * newr
    return t % q

def compute_roots(n: int, q: int, root: int) -> List[int]:
    roots = [1]
    omega = pow(root, (q - 1) // n, q)
    for _ in range(1, n):
        roots.append((roots[-1] * omega) % q)
    return roots

def ntt(a: np.ndarray, q: int, root: int) -> np.ndarray:
    n = len(a)
    a = bit_reverse_array(np.copy(a))
    roots = compute_roots(n, q, root)
    m = 1
    while m < n:
        step = n // (2 * m)
        for i in range(0, n, 2 * m):
            for j in range(m):
                u = a[i + j]
                v = a[i + j + m] * roots[j * step] % q
                a[i + j] = (u + v) % q
                a[i + j + m] = (u - v) % q
        m *= 2
    return a

def intt(a: np.ndarray, q: int, root: int) -> np.ndarray:
    n = len(a)
    a = bit_reverse_array(np.copy(a))
    inv_root = modinv(root, q)
    roots = compute_roots(n, q, inv_root)
    m = 1
    while m < n:
        step = n // (2 * m)
        for i in range(0, n, 2 * m):
            for j in range(m):
                u = a[i + j]
                v = a[i + j + m] * roots[j * step] % q
                a[i + j] = (u + v) % q
                a[i + j + m] = (u - v) % q
        m *= 2
    inv_n = modinv(n, q)
    return (a * inv_n) % q

def poly_mul_ntt(a: np.ndarray, b: np.ndarray, q: int, root: int) -> np.ndarray:
    a_ntt = ntt(a, q, root)
    b_ntt = ntt(b, q, root)
    c_ntt = (a_ntt * b_ntt) % q
    return intt(c_ntt, q, root)

# --------------------
# Poly
# --------------------

class Poly:
    def __init__(self, coeffs: List[int] | np.ndarray, n: int, q: int, root: int | None = None):
        self.n: int = n
        self.q: int = q
        self.root: int | None = root
        coeffs = np.array(coeffs, dtype=int) % q
        self.coeffs: np.ndarray = self._reduce_mod_xn1(coeffs)

    def _reduce_mod_xn1(self, coeffs: np.ndarray) -> np.ndarray:
        res = np.zeros(self.n, dtype=int)
        for i, c in enumerate(coeffs):
            if i < self.n:
                res[i] += c
            else:
                res[i % self.n] -= c
        return res % self.q

    def __add__(self, other: "Poly") -> "Poly":
        return Poly((self.coeffs + other.coeffs) % self.q, self.n, self.q, self.root)

    def __sub__(self, other: "Poly") -> "Poly":
        return Poly((self.coeffs - other.coeffs) % self.q, self.n, self.q, self.root)

    def __mul__(self, other: "Poly") -> "Poly":
        if self.root is None or other.root is None:
            raise ValueError("Primitive root not set for NTT multiplication.")
        result = poly_mul_ntt(self.coeffs, other.coeffs, self.q, self.root)
        return Poly(result, self.n, self.q, self.root)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Poly): return NotImplemented
        return np.array_equal(self.coeffs % self.q, other.coeffs % self.q)

    def __getitem__(self, idx: int) -> int:
        return self.coeffs[idx]

    def __setitem__(self, idx: int, val: int) :
        self.coeffs[idx] = val % self.q

    def __repr__(self) -> str:
        return f"Poly({self.coeffs.tolist()}, n={self.n}, q={self.q})"

    def as_list(self) -> List[int]:
        return self.coeffs.tolist()

    def norm_inf(self) -> int:
        centered = np.vectorize(lambda x: min(x, self.q - x))(self.coeffs % self.q)
        return int(np.max(centered))

    def copy(self) -> "Poly":
        return Poly(self.coeffs.copy(), self.n, self.q, self.root)

# --------------------
# PolyVec
# --------------------

class PolyVec:
    def __init__(self, polys: List[Poly]) :
        if not polys:
            raise ValueError("PolyVec must contain at least one Poly")

        self.n: int = polys[0].n
        self.q: int = polys[0].q
        self.root: int | None = polys[0].root

        for p in polys:
            if p.n != self.n or p.q != self.q:
                raise ValueError("All Polys in PolyVec must have the same n and q")
            if p.root != self.root:
                raise ValueError("All Polys in PolyVec must have the same NTT root")

        self.polys: List[Poly] = polys

    def __len__(self) -> int:
        return len(self.polys)

    def __getitem__(self, idx: int) -> Poly:
        return self.polys[idx]

    def __add__(self, other: "PolyVec") -> "PolyVec":
        return PolyVec([a + b for a, b in zip(self.polys, other.polys)])

    def __sub__(self, other: "PolyVec") -> "PolyVec":
        return PolyVec([a - b for a, b in zip(self.polys, other.polys)])

    def __mul__(self, scalar_poly: Poly) -> "PolyVec":
        return PolyVec([p * scalar_poly for p in self.polys])

    def as_matrix(self) -> List[np.ndarray]:
        return [p.coeffs for p in self.polys]

    def __repr__(self) -> str:
        return f"PolyVec([{', '.join(map(str, self.polys))}])"

# --------------------
# PolyMatrix
# --------------------

class PolyMatrix:
    def __init__(self, rows: List[List[Poly]]):
        self.rows: List[List[Poly]] = rows
        self.k: int = len(rows)
        self.l: int = len(rows[0])
        self.n: int = rows[0][0].n
        self.q: int = rows[0][0].q
        self.root: int | None = rows[0][0].root

    def __getitem__(self, idx: int) -> List[Poly]:
        return self.rows[idx]

    def matvec(self, vec: PolyVec) -> PolyVec:
        result: List[Poly] = []
        for row in self.rows:
            sum_poly = Poly(np.zeros(self.n), self.n, self.q, self.root)
            for p, v in zip(row, vec.polys):
                sum_poly += p * v
            result.append(sum_poly)
        return PolyVec(result)

    def __repr__(self) -> str:
        return f"PolyMatrix(rows={self.rows})"
