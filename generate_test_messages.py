import csv
import random
import string

def generate_random_word(min_length=3, max_length=10):
    """Generate a random word-like string with special characters and numbers."""
    length = random.randint(min_length, max_length)
    # Define character sets (excluding comma)
    vowels = 'aeiou'
    consonants = ''.join(c for c in string.ascii_lowercase if c not in vowels)
    numbers = string.digits
    special_chars = '!@#$%^&*()_+-=[]{}|;:<>.?/~`"\' '  # Excluding comma
    
    # Weight the character types (more letters than special chars)
    char_weights = [
        (consonants, 0.4),  # 40% consonants
        (vowels, 0.3),      # 30% vowels
        (numbers, 0.2),     # 20% numbers
        (special_chars, 0.1) # 10% special characters
    ]
    
    word = ''
    for _ in range(length):
        char_set, _ = random.choices(char_weights, weights=[w for _, w in char_weights])[0]
        word += random.choice(char_set)
    return word

def generate_random_message(word_count=20):
    """Generate a random message without commas."""
    words = [generate_random_word() for _ in range(word_count)]
    return ' '.join(words)

def get_next_char(c):
    """Get the next character in sequence, wrapping around if needed."""
    if c.isalpha():
        if c == 'z':
            return 'a'
        if c == 'Z':
            return 'A'
        return chr(ord(c) + 1)
    if c.isdigit():
        return str((int(c) + 1) % 10)
    return c

def create_modified_message(original):
    """Create a slightly modified version of the original message."""
    words = original.split()
    if len(words) < 2:
        return original + generate_random_word()
    
    # Randomly choose one of these modifications
    modification_type = random.choice(['swap', 'replace', 'remove', 'add', 'modify'])
    
    if modification_type == 'swap' and len(words) >= 2:
        i = random.randint(0, len(words) - 2)
        words[i], words[i + 1] = words[i + 1], words[i]
    elif modification_type == 'replace':
        i = random.randint(0, len(words) - 1)
        words[i] = generate_random_word()
    elif modification_type == 'remove':
        i = random.randint(0, len(words) - 1)
        words.pop(i)
    elif modification_type == 'modify':
        # Slightly modify an existing word by adding/removing/changing a character
        i = random.randint(0, len(words) - 1)
        word = words[i]
        if len(word) > 0:
            pos = random.randint(0, len(word) - 1)
            if random.random() < 0.33:  # Add
                words[i] = word[:pos] + generate_random_word(1, 1) + word[pos:]
            elif random.random() < 0.66:  # Remove
                words[i] = word[:pos] + word[pos+1:]
            else:  # Change
                words[i] = word[:pos] + generate_random_word(1, 1) + word[pos+1:]
    else:  # add
        i = random.randint(0, len(words))
        words.insert(i, generate_random_word())
    
    modified = ' '.join(words)
    
    # If modified message is identical to original, replace each character with next one
    if modified == original:
        modified = ''.join(get_next_char(c) for c in original)
    
    return modified

def generate_test_messages(num_messages=100):
    """Generate test messages and save them to CSV."""
    messages = []
    for _ in range(num_messages):
        original = generate_random_message()
        modified = create_modified_message(original)
        messages.append({'original': original, 'modified': modified})
    
    with open('test_messages.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['original', 'modified'])
        writer.writeheader()
        writer.writerows(messages)
    
    print(f"Generated {num_messages} test messages and saved to test_messages.csv")

if __name__ == '__main__':
    generate_test_messages(1000)