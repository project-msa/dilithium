from dilithium import ML_DSA

__all__ = ['ML_DSA_44', 'ML_DSA_65', 'ML_DSA_87']

_ML_DSA_44_PARAMS = {
    "d": 13,
    "tau": 39,
    "gamma_1": 131072,
    "gamma_2": 95232,
    "k": 4,
    "l": 4,
    "eta": 2,
    "omega": 80,
    "c_tilde_bytes": 32,
}

_ML_DSA_65_PARAMS = {
    "d": 13,
    "tau": 49,
    "gamma_1": 524288,
    "gamma_2": 261888,
    "k": 6,
    "l": 5,
    "eta": 4,
    "omega": 55,
    "c_tilde_bytes": 48,
}

_ML_DSA_87_PARAMS = {
    "d": 13,
    "tau": 60,
    "gamma_1": 524288,
    "gamma_2": 261888,
    "k": 8,
    "l": 7,
    "eta": 2,
    "omega": 75,
    "c_tilde_bytes": 64,
}

ML_DSA_44 = ML_DSA(_ML_DSA_44_PARAMS)
ML_DSA_65 = ML_DSA(_ML_DSA_65_PARAMS)
ML_DSA_87 = ML_DSA(_ML_DSA_87_PARAMS)