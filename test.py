import unittest
from params import ML_DSA_44, ML_DSA_65, ML_DSA_87
from colorama import init, Fore, Style
import sys

init(autoreset=True)

class ColoredTestResult(unittest.TestResult):
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super().__init__(stream, descriptions, verbosity)
        self.tests_run = 0
        self.total_tests = 0
        self.successes = []
        
    def startTest(self, test):
        self.tests_run += 1
        test_name = str(test).split(' ')[0]
        progress = f"[{self.tests_run}/{self.total_tests}]"
        sys.stdout.write(f"\r{Fore.CYAN}{progress} Running {test_name}...")
        sys.stdout.flush()
        super().startTest(test)
        
    def addSuccess(self, test):
        sys.stdout.write(f"\r{Fore.GREEN}✓ {str(test)} PASSED{' '*20}\n")
        self.successes.append(test)
        super().addSuccess(test)
        
    def addError(self, test, err):
        sys.stdout.write(f"\r{Fore.RED}⨯ {str(test)} ERROR: {err[1]}{' '*20}\n")
        super().addError(test, err)
        
    def addFailure(self, test, err):
        sys.stdout.write(f"\r{Fore.RED}⨯ {str(test)} FAILED: {err[1]}{' '*20}\n")
        super().addFailure(test, err)

class ColoredTestRunner(unittest.TextTestRunner):
    def run(self, test):
        result = ColoredTestResult()
        result.total_tests = test.countTestCases()
        print(f"{Fore.YELLOW}Running {result.total_tests} tests...\n")
        test(result)
        print(f"\n{Fore.CYAN}Results:{Style.RESET_ALL}")
        print(f"Tests run: {result.testsRun}")
        print(f"{Fore.GREEN}Successes: {len(result.successes)}")
        print(f"{Fore.RED}Failures: {len(result.failures)}")
        print(f"{Fore.RED}Errors: {len(result.errors)}")
        return result

class TestDilithium(unittest.TestCase):
    def setUp(self):
        # Initialize test message and context
        self.message = b"This is a test message"
        self.context = b"TEST"
        
        # Test different parameter sets
        self.schemes = {
            "ML-DSA-44": ML_DSA_44,
            "ML-DSA-65": ML_DSA_65,
            "ML-DSA-87": ML_DSA_87
        }

    def test_valid_signatures(self):
        """Test that valid signatures are correctly verified"""
        for name, scheme in self.schemes.items():
            with self.subTest(scheme=name):
                # Generate keypair
                pk, sk = scheme.keygen()
                
                # Sign message
                signature = scheme.sign(sk, self.message, self.context)
                
                # Verify signature
                result = scheme.verify(pk, self.message, signature, self.context)
                
                self.assertTrue(result, f"Valid signature verification failed for {name}")

    def test_invalid_signatures(self):
        """Test that invalid signatures are correctly rejected"""
        for name, scheme in self.schemes.items():
            with self.subTest(scheme=name):
                # Generate keypair
                pk, sk = scheme.keygen()
                
                # Sign message
                signature = scheme.sign(sk, self.message, self.context)
                
                # Modify message
                modified_message = b"Modified " + self.message
                
                # Verify with wrong message
                result = scheme.verify(pk, modified_message, signature, self.context)
                
                self.assertFalse(result, f"Invalid signature verification passed for {name}")

    def test_wrong_context(self):
        """Test that signatures with wrong context are rejected"""
        for name, scheme in self.schemes.items():
            with self.subTest(scheme=name):
                # Generate keypair
                pk, sk = scheme.keygen()
                
                # Sign message
                signature = scheme.sign(sk, self.message, self.context)
                
                # Verify with wrong context
                wrong_context = b"WRONG"
                result = scheme.verify(pk, self.message, signature, wrong_context)
                
                self.assertFalse(result, f"Wrong context verification passed for {name}")

    def test_wrong_public_key(self):
        """Test that signatures fail with wrong public key"""
        for name, scheme in self.schemes.items():
            with self.subTest(scheme=name):
                # Generate two keypairs
                pk1, sk1 = scheme.keygen()
                pk2, _ = scheme.keygen()
                
                # Sign with first secret key
                signature = scheme.sign(sk1, self.message, self.context)
                
                # Verify with second public key
                result = scheme.verify(pk2, self.message, signature, self.context)
                
                self.assertFalse(result, f"Wrong public key verification passed for {name}")

if __name__ == '__main__':
    runner = ColoredTestRunner()
    unittest.main(testRunner=runner)

