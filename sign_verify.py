import hashlib
from utils import *

def sign(sk: tuple[bytes, bytes, bytes, PolyVec, PolyVec, PolyVec],
         message: bytes,
         params: dict) -> tuple[PolyVec, list[np.ndarray], Poly]:
    """
    Full Dilithium signing with hint and deterministic y sampling.
    Returns (z, hint, c)
    """
    rho, K, tr, s1, s2, t0 = sk

    n        = params['n']
    q        = params['q']
    k        = params['k']
    l        = params['l']
    gamma1   = params['gamma1']
    gamma2   = params['gamma2']
    beta     = params['beta']
    omega    = params['omega']
    d        = params['d']
    root     = params['root']

    A = expand_A(rho, k, l, n, q, root)
    # print("A from key is : ", A)
    mu = hashlib.shake_256(tr + message).digest(64)
    nonce = 0

    while True:
        print("TRYING AGAIN")
        y = expand_mask(K, mu, nonce, l, n, gamma1, q, root)
        print(y)
        print(y.norm_inf())
        w = A * y
        w1 = highbits(w, 2 * gamma2)
        w1_bytes = b''.join(p.coeffs.astype(np.uint16).tobytes() for p in w1.polys)
        c = generate_challenge(mu + w1_bytes, n, q, root)
        print("hello")
        z = y + (c * s1)
        print(y,c,s1)
        print(z)
        print(z.norm_inf())
        if z.norm_inf() >= gamma1 - beta:
            nonce += 1
            print("didn't pass bruh")
            continue
        print("hello")
        cs2 = c * s2
        ct0 = c * t0
        w_prime = A * y - cs2 
        r_low = lowbits(w_prime, 2 * gamma2)
        print("hello")
        if r_low.norm_inf() >= gamma2 - beta:
            print("didn't pass second condition")
            nonce += 1
            continue
        print("hello")
        hint = make_hint_polyvec(ct0, w_prime, 2 * gamma2)
        h_weight = sum(np.sum(h) for h in hint)
        print("hello")
        if h_weight > omega:
            nonce += 1
            continue
        print("hello")
        return z, hint, c

def verify(pk: tuple[bytes, PolyVec],
           message: bytes,
           signature: tuple[PolyVec, list[np.ndarray], Poly],
           params: dict) -> bool:
    """
    Full Dilithium verification with hint usage.
    """
    rho, t1 = pk
    z, hint, c = signature

    n        = params['n']
    q        = params['q']
    k        = params['k']
    l        = params['l']
    gamma1   = params['gamma1']
    gamma2   = params['gamma2']
    omega    = params['omega']
    d        = params['d']
    root     = params['root']

    if z.norm_inf() >= gamma1 - params['beta']:
        return False

    t1_bytes = b''.join(p.coeffs.astype(np.uint16).tobytes() for p in t1.polys)
    tr = hashlib.shake_256(rho + t1_bytes).digest(32)
    mu = hashlib.shake_256(tr + message).digest(64)

    A = expand_A(rho, k, l, n, q, root)

    Az = A * z
    ct = c * t1
    ct_scaled = PolyVec([Poly((p.coeffs << d) % q, n, q, root) for p in ct.polys])
    if sum(np.sum(h) for h in hint) > omega:
        return False
    r = Az - ct_scaled
    w1_prime = use_hint_polyvec(hint, r, 2 * gamma2)

    w1_bytes = b''.join(p.coeffs.astype(np.uint16).tobytes() for p in w1_prime.polys)
    c_prime = generate_challenge(mu + w1_bytes, n, q, root)

    return c == c_prime