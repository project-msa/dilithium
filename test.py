from keygen import *
from sign_verify import *
def integration_test():
    params = {
        'n': 16,
        'q': 12289,
        'k': 2,
        'l': 2,
        'eta': 2,
        'gamma1': 64,
        'gamma2': 32,
        'beta': 4,
        'omega': 8,
        'd': 4,
        'root': 49  # primitive root for N=16, q=12289
    }

    print("🔑 Generating key pair...")
    pk, sk = keygen(params)
    print(pk, sk)
    message = b"hello from dilithium"
    print("✍️ Signing message:", message)
    signature = sign(sk, message, params)

    print("✅ Verifying signature...")
    valid = verify(pk, message, signature, params)
    print("Result:", "✔️ Valid" if valid else "❌ Invalid")

    # Negative test 1: Tampered message
    print("🧪 Tampering with message...")
    tampered_message = b"hello from attacker"
    valid = verify(pk, tampered_message, signature, params)
    print("Tampered message check:", "✔️ Detected" if not valid else "❌ Missed")

    # Negative test 2: Tampered signature (flip one coefficient)
    print("🧪 Tampering with signature...")
    print(len(signature))
    z, h,  c = signature
    z_tampered = z.copy()
    z_tampered[0][0] = (z_tampered[0][0] + 1) % params['q']
    tampered_sig = (z_tampered, h, c)
    valid = verify(pk, message, tampered_sig, params)
    print("Tampered signature check:", "✔️ Detected" if not valid else "❌ Missed")

integration_test()