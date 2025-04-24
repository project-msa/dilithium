import os
import numpy as np
import hashlib
from utils import *  

def keygen(params: dict) -> tuple[tuple[bytes, PolyVec], tuple[bytes, bytes, bytes, PolyVec, PolyVec, PolyVec]]:
    """
    Generates a public/secret key pair for the Dilithium scheme.
    """
    n    = params['n']
    q    = params['q']
    k    = params['k']
    l    = params['l']
    eta  = params['eta']
    d    = params['d']
    root = params['root']

    # Sample uniform random seeds
    rho = os.urandom(32)  # Seed for generating matrix A
    K   = os.urandom(32)  # Secret key seed for signing

    # Generate matrix A from rho
    A = expand_A(rho, k, l, n, q, root)

    # Sample short secret vectors s1 ∈ S_η^ℓ and s2 ∈ S_η^k
    s1 = sample_small_polyvec(l, n, eta, q, root)
    s2 = sample_small_polyvec(k, n, eta, q, root)
    print("S1 is ",s1)
    print("S2 is ",s2)
    # Compute t = A * s1 + s2
    t = A * s1 + s2
    print("A from matrix multiplication is : ", A)
    # Split t into high bits (t1) and low bits (t0)
    t1, t0 = power2round(t, d)

    # Compute tr = SHAKE256(rho || t1)
    t1_bytes = b''.join(p.coeffs.astype(np.uint16).tobytes() for p in t1.polys)
    tr = hashlib.shake_256(rho + t1_bytes).digest(32)

    pk = (rho, t1)
    sk = (rho, K, tr, s1, s2, t0)
    return pk, sk

if __name__ == "__main__":
    params = {
        'n': 16,
        'q': 12289,
        'k': 2,
        'l': 2,
        'eta': 1,
        'gamma1': 64,
        'gamma2': 32,
        'beta': 8,
        'omega': 8,
        'd': 4,
        'root': 49  # primitive root for N=16, q=12289
    }
    keygen(params)
