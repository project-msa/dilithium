import csv
import time
from statistics import mean
from params import ML_DSA_44, ML_DSA_65, ML_DSA_87
from tabulate import tabulate
from colorama import init, Fore, Style
from tqdm import tqdm

def validate_message(message):
    return ',' not in message

def run_performance_tests():
    # Initialize colorama
    init()

    # Load test messages from CSV
    messages = []
    print(f"{Fore.CYAN}Loading test messages...{Style.RESET_ALL}")
    try:
        with open('test_messages.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not validate_message(row['original']) or not validate_message(row['modified']):
                    print(f"{Fore.RED}Warning: Found message containing commas, skipping: {row['original'][:30]}...{Style.RESET_ALL}")
                    continue
                messages.append((row['original'].encode(), row['modified'].encode()))
    except csv.Error as e:
        print(f"{Fore.RED}Error reading CSV file: {e}{Style.RESET_ALL}")
        return

    if not messages:
        print(f"{Fore.RED}No valid test messages found in CSV file{Style.RESET_ALL}")
        return

    schemes = {
        "ML-DSA-44": ML_DSA_44,
        "ML-DSA-65": ML_DSA_65,
        "ML-DSA-87": ML_DSA_87
    }

    results = []
    stats = []
    context = b"TEST"
    
    # Store failing cases for analysis
    failing_cases = {}

    for name, scheme in schemes.items():
        print(f"\n{Fore.GREEN}Testing {name}...{Style.RESET_ALL}")
        keygen_times = []
        sign_times = []
        verify_times = []
        verify_invalid_times = []
        
        # Statistics for verification results
        false_positives = 0
        false_negatives = 0
        failing_cases[name] = []

        progress_bar = tqdm(messages, desc=f"{name} Progress", unit="msg")
        for orig_msg, mod_msg in progress_bar:
            # Time key generation
            start = time.time()
            pk, sk = scheme.keygen()
            keygen_times.append(time.time() - start)

            # Time signing
            start = time.time()
            signature = scheme.sign(sk, orig_msg)
            sign_times.append(time.time() - start)

            # Time valid verification and check correctness
            start = time.time()
            try:
                valid_result = scheme.verify(pk, orig_msg, signature)
                if not valid_result:
                    false_negatives += 1
                    failing_cases[name].append({
                        'message': orig_msg.decode(),
                        'type': 'false_negative',
                        'error': 'Verification returned False'
                    })
            except Exception as e:
                false_negatives += 1
                failing_cases[name].append({
                    'message': orig_msg.decode(),
                    'type': 'false_negative',
                    'error': str(e)
                })
            verify_times.append(time.time() - start)

            # Time invalid verification and check correctness
            start = time.time()
            try:
                invalid_result = scheme.verify(pk, mod_msg, signature, context)
                if invalid_result:
                    false_positives += 1
                    failing_cases[name].append({
                        'message': mod_msg.decode(),
                        'type': 'false_positive',
                        'error': 'Verification returned True for invalid signature'
                    })
            except:
                pass  # Expected failure for invalid signature
            verify_invalid_times.append(time.time() - start)

        avg_keygen = mean(keygen_times) * 1000
        avg_sign = mean(sign_times) * 1000
        avg_verify = mean(verify_times) * 1000
        avg_verify_invalid = mean(verify_invalid_times) * 1000

        results.append([
            f"{Fore.GREEN}{name}{Style.RESET_ALL}",
            f"{avg_keygen:.2f}",
            f"{avg_sign:.2f}",
            f"{avg_verify:.2f}",
            f"{avg_verify_invalid:.2f}"
        ])

        stats.append([
            f"{Fore.GREEN}{name}{Style.RESET_ALL}",
            false_positives,
            false_negatives,
            len(messages)
        ])

    # Print performance results table
    print(f"\n{Fore.CYAN}Performance Results:{Style.RESET_ALL}")
    headers = ["Scheme", "Keygen (ms)", "Sign (ms)", "Verify Valid (ms)", "Verify Invalid (ms)"]
    print(tabulate(results, headers=headers, tablefmt="grid"))

    # Print verification statistics
    print(f"\n{Fore.CYAN}Verification Statistics:{Style.RESET_ALL}")
    stat_headers = ["Scheme", "False Positives", "False Negatives", "Total Tests"]
    print(tabulate(stats, stat_headers, tablefmt="grid"))

    # Print summary of verification results
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    for row in stats:
        scheme = row[0]
        fp = row[1]
        fn = row[2]
        total = row[3]
        
        if fp == 0 and fn == 0:
            print(f"{scheme}: {Fore.GREEN}All verifications passed correctly{Style.RESET_ALL}")
        else:
            print(f"{scheme}:")
            if fn > 0:
                print(f"{Fore.RED}  ⚠ {fn} false negatives (rejected valid signatures){Style.RESET_ALL}")
                print(f"\n{Fore.YELLOW}Failed Messages for {scheme} - False Negatives:{Style.RESET_ALL}")
                for case in failing_cases[scheme]:
                    if case['type'] == 'false_negative':
                        print(f"  Message: {case['message'][:50]}...")
                        print(f"  Error: {case['error']}\n")
            if fp > 0:
                print(f"{Fore.RED}  ⚠ {fp} false positives (accepted invalid signatures){Style.RESET_ALL}")
                print(f"\n{Fore.YELLOW}Failed Messages for {scheme} - False Positives:{Style.RESET_ALL}")
                for case in failing_cases[scheme]:
                    if case['type'] == 'false_positive':
                        print(f"  Message: {case['message'][:50]}...")
                        print(f"  Error: {case['error']}\n")

if __name__ == '__main__':
    run_performance_tests()