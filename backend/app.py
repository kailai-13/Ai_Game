from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import os
from typing import Dict, List, Any
import logging
import random
import re

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Groq API configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# Check if API key is loaded
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables!")
    print("WARNING: GROQ_API_KEY not found. Please check your .env file.")

def call_groq_api(prompt: str) -> str:
    """Call Groq API with the given prompt"""
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set")
        return ""
    
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'model': 'llama3-8b-8192',
        'temperature': 0.3,
        'max_tokens': 500,
        'top_p': 1.0,
        'stream': False
    }
    
    try:
        logger.info(f"Making request to Groq API with model: {data['model']}")
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        
        logger.info(f"Groq API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            return ""
            
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        logger.info(f"Groq API response received successfully")
        return content
        
    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error calling Groq API: {e}")
        return ""
    except KeyError as e:
        logger.error(f"Unexpected response format from Groq API: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error calling Groq API: {e}")
        return ""

def generate_multiple_choice_spelling(word: str) -> Dict[str, Any]:
    """Generate multiple choice spelling challenge with human-like mistakes"""
    prompt = f"""Create a multiple choice spelling challenge for the word "{word}".

Generate 3 very tempting misspellings that humans would commonly make and that look almost correct:
- Make them sound identical when spoken
- Use the most common spelling mistakes for this specific word
- Make them visually similar to the correct spelling
- Focus on the parts of the word that are most commonly misspelled

For example, if the word is "beautiful", wrong options could be "beatiful", "beautifull", "beutiful"

Respond with ONLY valid JSON in this exact format:
{{
    "correct": "{word}",
    "options": ["{word}", "tempting_misspelling1", "tempting_misspelling2", "tempting_misspelling3"]
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for word '{word}': {e}")
            logger.error(f"Response was: {response}")


    # Enhanced fallback with very tempting, human-like mistakes
    word_lower = word.lower()
    tempting_mistakes = set() # Use a set to automatically handle duplicates
    
    # Create specific tempting misspellings based on common patterns
    
    # 1. Double letter confusions
    for i in range(len(word_lower) - 1):
        if word_lower[i] != word_lower[i + 1]:  # Add double letter
            mistake = word_lower[:i + 1] + word_lower[i] + word_lower[i + 1:]
            if len(mistake) <= len(word_lower) + 1: # Avoid excessively long words
                tempting_mistakes.add(mistake)
        elif word_lower[i] == word_lower[i + 1]:  # Remove double letter
            mistake = word_lower[:i] + word_lower[i + 1:]
            if len(mistake) >= 3: # Avoid too short words
                tempting_mistakes.add(mistake)
    
    # 2. Common vowel confusions that sound similar
    vowel_confusions = [
        ('ie', 'ei'), ('ei', 'ie'),  # receive/recieve
        ('ea', 'ee'), ('ee', 'ea'),  # breath/breathe
        ('ou', 'ow'), ('ow', 'ou'),  # through/throw
        ('ai', 'ay'), ('ay', 'ai'),  # main/mayn
        ('au', 'aw'), ('aw', 'au'),  # cause/caws
        ('e', 'a'), ('a', 'e'), # separate/seperate
        ('o', 'a'), ('a', 'o'), # familiar/familar
    ]
    
    for original, replacement in vowel_confusions:
        if original in word_lower:
            # Replace only the first occurrence for distinct mistakes
            mistake = word_lower.replace(original, replacement, 1)
            if mistake != word_lower:
                tempting_mistakes.add(mistake)
    
    # 3. Silent letter mistakes (removing or adding a common silent letter)
    silent_letter_patterns = {
        'kn': 'n', 'wr': 'r', 'mb': 'm', 'bt': 't', # Remove silent letter
        'ght': 'gt', # Common reduction
        'dge': 'ge', # Common reduction
        'tch': 'ch', # Common reduction
    }
    
    for pattern, replacement in silent_letter_patterns.items():
        if pattern in word_lower:
            mistake = word_lower.replace(pattern, replacement, 1)
            if mistake != word_lower and len(mistake) >= 3:
                tempting_mistakes.add(mistake)
    
    # Adding silent letters where they don't belong (simple cases)
    if not word_lower.endswith('e') and len(word_lower) > 2:
        tempting_mistakes.add(word_lower + 'e') # Add silent 'e'
    
    # 4. Common ending confusions
    ending_confusions = [
        ('ful', 'full'), ('full', 'ful'),
        ('ly', 'ley'), ('ley', 'ly'),
        ('ance', 'ence'), ('ence', 'ance'),
        ('ant', 'ent'), ('ent', 'ant'),
        ('tion', 'sion'), ('sion', 'tion'),
        ('able', 'ible'), ('ible', 'able'),
        ('ous', 'ious'), ('ious', 'ous'),
        ('ment', 'mant'), ('ment', 'munt'),
    ]
    
    for original, replacement in ending_confusions:
        if word_lower.endswith(original):
            mistake = word_lower[:-len(original)] + replacement
            tempting_mistakes.add(mistake)
    
    # 5. Phonetic mistakes (letters that sound similar)
    phonetic_confusions = [
        ('c', 'k'), ('k', 'c'),  # cat/kat, keep/ceep
        ('s', 'c'), ('c', 's'),  # since/cinse, cycle/sycel
        ('f', 'ph'), ('ph', 'f'),  # phone/fone, fun/phun
        ('j', 'g'), ('g', 'j'),   # judge/gudge, gem/jem
        ('z', 's'), ('s', 'z'),   # please/pleaze, rise/rize
        ('x', 'cs'), ('cs', 'x'), # excellent/ecsellent
    ]
    
    for original, replacement in phonetic_confusions:
        if original in word_lower:
            mistake = word_lower.replace(original, replacement, 1)
            if mistake != word_lower:
                tempting_mistakes.add(mistake)
    
    # 6. Letter transposition (swapping adjacent letters)
    if len(word_lower) > 2:
        for i in range(len(word_lower) - 1):
            if word_lower[i] != word_lower[i + 1]: # Avoid swapping identical letters
                mistake_list = list(word_lower)
                mistake_list[i], mistake_list[i+1] = mistake_list[i+1], mistake_list[i]
                tempting_mistakes.add("".join(mistake_list))
    
    # Convert set to list, ensuring no duplicate of the correct word
    tempting_mistakes = list(tempting_mistakes - {word_lower}) # Remove the correct word if it ended up in mistakes

    # Ensure we have enough unique and distinct tempting mistakes
    final_options = [word] 
    
    # Prioritize shorter, more common errors
    tempting_mistakes_sorted = sorted(list(tempting_mistakes), key=lambda x: (abs(len(x) - len(word_lower)), x))

    for mistake in tempting_mistakes_sorted:
        if len(final_options) < 4:
            # Check for high similarity to the correct word (e.g., Levenshtein distance)
            # A simple way for now: ensure it's not too different in length or character count
            if abs(len(mistake) - len(word_lower)) <= 2: # Max 2 chars diff
                final_options.append(mistake)
        else:
            break
            
    # Fallback to generic mistakes if still not enough unique tempting options
    while len(final_options) < 4:
        new_mistake = ""
        if len(word_lower) > 2:
            # Simple letter deletion or insertion
            if random.random() < 0.5: # Deletion
                idx = random.randint(0, len(word_lower) - 1)
                new_mistake = word_lower[:idx] + word_lower[idx+1:]
            else: # Insertion
                idx = random.randint(0, len(word_lower))
                new_mistake = word_lower[:idx] + random.choice('aeiou') + word_lower[idx:]
        else: # For very short words, just add/remove a letter
            new_mistake = word_lower + random.choice('s') if random.random() < 0.5 else word_lower[:-1]
        
        if new_mistake and new_mistake != word_lower and new_mistake not in final_options:
            final_options.append(new_mistake)

    random.shuffle(final_options)
    
    return {
        "correct": word,
        "options": final_options[:4]
    }

def generate_suffix_completion(word: str) -> Dict[str, Any]:
    """Generate suffix completion challenge with confusing suffixes"""
    if len(word) <= 4:
        base_word = word[:-2] if len(word) > 2 else word[:-1]
    else:
        base_word = word[:-3]
    
    correct_suffix = word[len(base_word):]
    
    prompt = f"""Create a suffix completion challenge for the word "{word}".
The base word is "{base_word}" and the correct suffix is "{correct_suffix}".

Generate 3 very tempting misspellings of the correct suffix that humans would commonly confuse:
- Make them sound identical or very similar when spoken
- Use common spelling mistakes for this specific suffix
- Make them look plausible and realistic

For example, if the correct suffix is "ful", wrong options could be "full", "fole", "fule"

Return ONLY the suffix options, not complete words.

Respond with ONLY valid JSON in this exact format:
{{
    "base_word": "{base_word}",
    "correct_suffix": "{correct_suffix}",
    "options": ["{correct_suffix}", "tempting_misspelling1", "tempting_misspelling2", "tempting_misspelling3"]
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('``````', '')
            
            result = json.loads(cleaned_response)
            # Ensure we only return suffixes, not full words
            # This logic needs to be careful, as the LLM might return full words if not prompted precisely enough.
            # Assuming the prompt guides it to return suffixes, we just ensure they are strings.
            # No need for this complex opt.startswith(base_word) if prompt is followed.
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for suffix completion '{word}': {e}")
            logger.error(f"Response was: {response}")

    
    # Enhanced fallback with more tempting, human-like mistakes
    confusing_suffixes = set() # Use set to handle duplicates
    
    # Create very tempting misspellings based on the actual suffix
    if correct_suffix == 'ful':
        confusing_suffixes.update(['full', 'fole', 'fule'])
    elif correct_suffix == 'tion':
        confusing_suffixes.update(['sion', 'shun', 'tian'])
    elif correct_suffix == 'sion':
        confusing_suffixes.update(['tion', 'shun', 'sian'])
    elif correct_suffix == 'able':
        confusing_suffixes.update(['ible', 'abel', 'abul'])
    elif correct_suffix == 'ible':
        confusing_suffixes.update(['able', 'ibel', 'ibul'])
    elif correct_suffix == 'ous':
        confusing_suffixes.update(['ious', 'eous', 'ouse'])
    elif correct_suffix == 'ious':
        confusing_suffixes.update(['ous', 'eous', 'iouse'])
    elif correct_suffix == 'ly':
        confusing_suffixes.update(['ley', 'lie', 'lee'])
    elif correct_suffix == 'ing':
        confusing_suffixes.update(['eing', 'yng', 'ine'])
    elif correct_suffix == 'ed':
        confusing_suffixes.update(['id', 'ead', 'ded'])
    elif correct_suffix == 'er':
        confusing_suffixes.update(['or', 'ar', 'ere'])
    elif correct_suffix == 'or':
        confusing_suffixes.update(['er', 'ore', 'our'])
    elif correct_suffix == 'ant':
        confusing_suffixes.update(['ent', 'andt', 'ante'])
    elif correct_suffix == 'ent':
        confusing_suffixes.update(['ant', 'ente', 'emt'])
    elif correct_suffix == 'ment':
        confusing_suffixes.update(['mant', 'memt', 'mnet'])
    elif correct_suffix == 'ness':
        confusing_suffixes.update(['nes', 'nees', 'niss'])
    elif correct_suffix == 'less':
        confusing_suffixes.update(['les', 'lees', 'liss'])
    elif correct_suffix == 'ward':
        confusing_suffixes.update(['werd', 'wared', 'werd'])
    
    # Generic phonetic variations for other suffixes
    if len(correct_suffix) >= 2:
        # Swap vowels
        vowels = 'aeiou'
        for i, char in enumerate(correct_suffix):
            if char in vowels:
                other_vowels = [v for v in vowels if v != char]
                if other_vowels:
                    temp_list = list(correct_suffix)
                    temp_list[i] = random.choice(other_vowels)
                    confusing_suffixes.add("".join(temp_list))
        
        # Add/remove single letter
        if len(correct_suffix) > 1:
            confusing_suffixes.add(correct_suffix[:-1])
        confusing_suffixes.add(correct_suffix + random.choice('aeiou'))

        # Transposition
        if len(correct_suffix) > 1:
            idx = random.randint(0, len(correct_suffix) - 2)
            transposed = list(correct_suffix)
            transposed[idx], transposed[idx+1] = transposed[idx+1], transposed[idx]
            confusing_suffixes.add("".join(transposed))

    # Ensure no duplicates with correct suffix
    confusing_suffixes.discard(correct_suffix)
    
    final_options = [correct_suffix] + list(confusing_suffixes)[:3]
    random.shuffle(final_options)
    
    return {
        "base_word": base_word,
        "correct_suffix": correct_suffix,
        "options": final_options[:4]
    }

def generate_fill_blanks(word: str) -> Dict[str, Any]:
    """Generate fill in the blanks challenge with exactly 2 consecutive letters"""
    if len(word) < 3:
        # Fallback for very short words, might need adjustment based on desired behavior
        # Since the original request specified "exactly 2 consecutive letters",
        # words shorter than 3 cannot fulfill this.
        # Here, it blanks the last letter if word is 2 chars, or returns the word if 1 char.
        blanked_word_short = word[0] + '__' if len(word) == 2 else word
        missing_letters_short = word[1:] if len(word) == 2 else word # Example: for 'at', missing is 't'
        
        return {
            "blanked_word": blanked_word_short,
            "correct_answer": word,
            "missing_letters": missing_letters_short,
            "options": [missing_letters_short, "ab", "cd", "ef"][:4] # Provide generic 2-letter combos
        }
    
    # Find the best position for 2 consecutive blanks
    # Prioritize positions that contain common problem areas
    problem_patterns = ['ie', 'ei', 'ou', 'ea', 'oo', 'ee', 'ss', 'll', 'nn', 'mm', 'tt', 'ch', 'sh', 'th', 'ph']
    
    # Look for problem patterns first
    best_position = -1
    random.shuffle(problem_patterns) # Shuffle to give different patterns a chance
    for pattern in problem_patterns:
        # Find all occurrences of the pattern
        starts = [m.start() for m in re.finditer(pattern, word.lower())]
        # Choose a random start position from valid ones
        valid_starts = [s for s in starts if s + 2 <= len(word)]
        if valid_starts:
            best_position = random.choice(valid_starts)
            break
    
    # If no problem patterns found or suitable position, choose a position avoiding start and end
    if best_position == -1:
        if len(word) >= 4:
            # Blank two letters from middle to avoid start/end, prioritizing non-vowel/vowel combos
            possible_starts = [i for i in range(1, len(word) - 2)] # Not at very beginning or end
            if possible_starts:
                best_position = random.choice(possible_starts)
            else:
                best_position = 0 # Fallback for very short words like 3-letter
        else: # For 3-letter words, blank middle two
            best_position = 0 if len(word) == 3 else 0 # Should only happen if len(word) < 3 originally
            

    # Create blanked word with exactly 2 consecutive blanks
    blanked_word = word[:best_position] + "__" + word[best_position + 2:]
    missing_letters = word[best_position:best_position + 2].lower()
    
    prompt = f"""Create a fill-in-the-blanks challenge for the word "{word}".
The blanked version is "{blanked_word}" where the missing letters are "{missing_letters}".

Generate 3 very tempting misspellings of the correct 2-letter combination that humans would commonly confuse:
- Make them sound identical or very similar when spoken
- Use common spelling mistakes for these specific letters
- Make them look plausible and realistic

For example, if correct is "ie", wrong options could be "ei", "ee", "ea"
If correct is "ou", wrong options could be "ow", "oo", "au"

Return ONLY the 2-letter combinations, NOT complete words.

Respond with ONLY valid JSON in this exact format:
{{
    "blanked_word": "{blanked_word}",
    "correct_answer": "{word}",
    "missing_letters": "{missing_letters}",
    "options": ["{missing_letters}", "tempting_combo1", "tempting_combo2", "tempting_combo3"]
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```
                cleaned_response = cleaned_response.replace('```json', '').replace('```
                
            result = json.loads(cleaned_response)
            # Ensure options are only 2-letter combinations
            # This assumes the LLM will return 2-letter strings.
            # No need for this complex opt[:2] if prompt is followed.
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for fill blanks '{word}': {e}")
            logger.error(f"Response was: {response}")
    
    # Enhanced fallback with very tempting letter combinations
    confusing_combos = set() # Use a set to manage uniqueness
    
    # Create very tempting misspellings based on the actual missing letters
    # Prioritize specific common errors
    common_pairs = {
        'ie': ['ei', 'ee', 'ea'], 'ei': ['ie', 'ai', 'ee'],
        'ou': ['ow', 'oo', 'au'], 'ow': ['ou', 'oo', 'aw'],
        'ea': ['ee', 'ie', 'ai'], 'ee': ['ea', 'ie', 'ei'],
        'oo': ['ou', 'ow', 'ue'], 'ai': ['ei', 'ay', 'ae'],
        'ay': ['ai', 'ey', 'ae'], 'ey': ['ay', 'ei', 'ie'],
        'au': ['aw', 'ou', 'ao'], 'aw': ['au', 'ow', 'ao'],
        'll': ['le', 'el', 'l'], 'ss': ['se', 'es', 's'],
        'nn': ['ne', 'en', 'n'], 'mm': ['me', 'em', 'm'],
        'tt': ['te', 'et', 't'], 'rr': ['re', 'er', 'r'],
        'ck': ['k', 'ch', 'cc'], 'ch': ['tch', 'sh', 'c'],
        'sh': ['ch', 'tsch', 'zh'], 'th': ['dh', 'f', 'v'],
        'ph': ['f', 'gh', 'v']
    }

    if missing_letters in common_pairs:
        confusing_combos.update(common_pairs[missing_letters])
    else:
        # Fallback for less common pairs
        first_letter = missing_letters
        second_letter = missing_letters

        # 1. Swap letters if different
        if first_letter != second_letter:
            confusing_combos.add(second_letter + first_letter)

        # 2. Change one letter (vowel/consonant swap)
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        
        # Change first letter
        if first_letter in vowels:
            possible_swaps = [v for v in vowels if v != first_letter]
            if possible_swaps: confusing_combos.add(random.choice(possible_swaps) + second_letter)
        elif first_letter in consonants:
            possible_swaps = [c for c in consonants if c != first_letter]
            if possible_swaps: confusing_combos.add(random.choice(possible_swaps) + second_letter)

        # Change second letter
        if second_letter in vowels:
            possible_swaps = [v for v in vowels if v != second_letter]
            if possible_swaps: confusing_combos.add(first_letter + random.choice(possible_swaps))
        elif second_letter in consonants:
            possible_swaps = [c for c in consonants if c != second_letter]
            if possible_swaps: confusing_combos.add(first_letter + random.choice(possible_swaps))

        # 3. Double one of the letters if not already double
        if first_letter != second_letter:
            confusing_combos.add(first_letter * 2)
            confusing_combos.add(second_letter * 2)
        
        # 4. Add a common third letter and truncate
        if len(missing_letters) == 2:
            confusing_combos.add(missing_letters + random.choice(vowels))
            confusing_combos.add(random.choice(vowels) + missing_letters)

    # Ensure all generated combos are exactly 2 characters and not the correct answer
    confusing_combos_filtered = {c for c in confusing_combos if len(c) == 2 and c != missing_letters}

    # Populate options, ensuring 3 unique tempting alternatives
    final_options = [missing_letters]
    for combo in list(confusing_combos_filtered): # Convert to list to iterate
        if len(final_options) < 4:
            final_options.append(combo)
        else:
            break
            
    # If still not enough, generate more generic but valid 2-letter combos
    all_possible_two_letter_combos = [a+b for a in 'abcdefghijklmnopqrstuvwxyz' for b in 'abcdefghijklmnopqrstuvwxyz']
    random.shuffle(all_possible_two_letter_combos)
    
    for combo in all_possible_two_letter_combos:
        if len(final_options) < 4 and combo not in final_options:
            final_options.append(combo)
        elif len(final_options) == 4:
            break

    random.shuffle(final_options)
    
    return {
        "blanked_word": blanked_word,
        "correct_answer": word,
        "missing_letters": missing_letters,
        "options": final_options[:4]
    }


def generate_error_detection(word: str) -> Dict[str, Any]:
    """Generate error detection challenge with subtle, tempting mistakes"""
    prompt = f"""Create an error detection challenge for the word "{word}".

Generate ONE subtle, realistic misspelling that humans might easily overlook:
- Use common mistakes like ei/ie confusion, silent letter errors, double letter issues
- Make it subtle enough that it looks almost correct at first glance
- Focus on the most commonly misspelled parts of words

Respond with ONLY valid JSON in this exact format:
{{
    "original_word": "{word}",
    "misspelled_word": "subtle_misspelling"
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('``````', '').strip()
                
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for error detection '{word}': {e}")
            logger.error(f"Response was: {response}")
    
    # Enhanced fallback with subtle mistakes
    word_lower = word.lower()
    misspelled = ""
    
    # Try different types of subtle mistakes (prioritized for realism)
    # 1. ei/ie confusion
    if 'ie' in word_lower:
        misspelled = word_lower.replace('ie', 'ei', 1)
    elif 'ei' in word_lower:
        misspelled = word_lower.replace('ei', 'ie', 1)
    
    # 2. Common double letter errors (remove one or add one)
    if not misspelled:
        for i in range(len(word_lower) - 1):
            if word_lower[i] == word_lower[i + 1]: # Remove a double letter
                misspelled = word_lower[:i] + word_lower[i + 1:]
                break
            elif i < len(word_lower) - 2: # Add a double letter (e.g., comittee -> committee)
                if word_lower[i+1] == word_lower[i+2]: # if next two are same, try adding one of current
                    misspelled = word_lower[:i+1] + word_lower[i+1] + word_lower[i+1:]
                    break
        
    # 3. Silent letter errors (e.g., removing 'k' from 'knife', adding 'e' to 'recieve')
    if not misspelled and len(word_lower) > 3:
        if 'kn' in word_lower:
            misspelled = word_lower.replace('kn', 'n', 1)
        elif 'gh' in word_lower:
            misspelled = word_lower.replace('gh', 'g', 1)
        elif not word_lower.endswith('e') and random.random() < 0.5:
             misspelled = word_lower + 'e'
        elif word_lower.endswith('e') and random.random() < 0.5 and len(word_lower) > 3:
            misspelled = word_lower[:-1]

    # 4. Vowel confusion (e.g., 'a' for 'e' in 'separate')
    if not misspelled:
        vowel_swaps_subtle = [('a', 'e'), ('e', 'a'), ('o', 'u'), ('u', 'o')]
        for original, replacement in vowel_swaps_subtle:
            if original in word_lower:
                temp_misspelled = word_lower.replace(original, replacement, 1)
                if temp_misspelled != word_lower and len(temp_misspelled) == len(word_lower):
                    misspelled = temp_misspelled
                    break

    # 5. Simple transposition (swapping two adjacent letters)
    if not misspelled and len(word_lower) > 2:
        idx = random.randint(0, len(word_lower) - 2)
        misspelled_list = list(word_lower)
        misspelled_list[idx], misspelled_list[idx+1] = misspelled_list[idx+1], misspelled_list[idx]
        misspelled = "".join(misspelled_list)
        
    # Final fallback if no subtle mistake was generated
    if not misspelled or misspelled == word_lower:
        if len(word_lower) > 3:
            pos = random.randint(1, len(word_lower) - 2)
            misspelled = word_lower[:pos] + random.choice('aeiou') + word_lower[pos + 1:] # Change a middle letter
        else:
            misspelled = word_lower + random.choice('s') # Append a letter

    return {
        "original_word": word,
        "misspelled_word": misspelled
    }


def generate_guided_completion(word: str) -> Dict[str, Any]:
    """Generate guided word completion challenge with strategic blanks"""
    # Create more strategic incomplete word (remove middle part, keep beginning and end)
    if len(word) <= 4:
        incomplete_word = word[:1] + "_" * (len(word) - 2) + word[-1:]
    elif len(word) <= 6:
        incomplete_word = word[:2] + "_" * (len(word) - 4) + word[-2:]
    else:
        incomplete_word = word[:2] + "_" * (len(word) - 5) + word[-3:]
    
    prompt = f"""Create a guided word completion challenge for the word "{word}".
The incomplete word is "{incomplete_word}".

Provide a helpful but not too obvious hint about the word's meaning, usage, or context.
The hint should guide the player without giving away the answer directly.

Respond with ONLY valid JSON in this exact format:
{{
    "incomplete_word": "{incomplete_word}",
    "hint": "helpful but challenging hint about the word",
    "correct_completion": "{word}"
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```
                cleaned_response = cleaned_response.replace('```json', '').replace('```
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for guided completion '{word}': {e}")
            logger.error(f"Response was: {response}")

    
    # Enhanced fallback with better hints
    hints = [
        f"This {len(word)}-letter word starts with '{word}' and ends with '{word[-1]}'",
        f"A word that rhymes with '{word[:-1]}e'",
        f"This word contains {len([c for c in word if c in 'aeiou'])} vowel(s)",
        f"Think of a word related to the pattern '{word[:2]}...{word[-2:]}'"
    ]
    
    return {
        "incomplete_word": incomplete_word,
        "hint": random.choice(hints),
        "correct_completion": word
    }

@app.route('/api/generate-game', methods=['POST'])
def generate_game():
    """Generate game content for a specific word and game type"""
    data = request.get_json()
    
    if not data or 'word' not in data or 'game_type' not in data:
        return jsonify({'error': 'Word and game_type are required'}), 400
    
    word = data['word'].strip().lower()
    game_type = data['game_type']
    
    if not word:
        return jsonify({'error': 'Word cannot be empty'}), 400
    
    logger.info(f"Generating {game_type} game for word: {word}")
    
    try:
        if game_type == 'multiple_choice_spelling':
            result = generate_multiple_choice_spelling(word)
        elif game_type == 'suffix_completion':
            result = generate_suffix_completion(word)
        elif game_type == 'fill_blanks':
            result = generate_fill_blanks(word)
        elif game_type == 'error_detection':
            result = generate_error_detection(word)
        elif game_type == 'guided_completion':
            result = generate_guided_completion(word)
        else:
            return jsonify({'error': 'Invalid game type'}), 400
        
        return jsonify({
            'word': word,
            'game_type': game_type,
            'game_data': result
        })
    
    except Exception as e:
        logger.error(f"Error generating game for word '{word}': {e}")
        return jsonify({'error': f'Failed to generate game: {str(e)}'}), 500

@app.route('/api/generate-all-games', methods=['POST'])
def generate_all_games():
    """Generate all games for a list of words with their assigned game types"""
    data = request.get_json()
    
    if not data or 'words' not in data:
        return jsonify({'error': 'Words array is required'}), 400
    
    words_data = data['words']
    results = []
    
    logger.info(f"Received request to generate games for {len(words_data)} words")
    
    for word_item in words_data:
        if 'word' not in word_item or 'game_type' not in word_item:
            continue
            
        word = word_item['word'].strip().lower()
        game_type = word_item['game_type']
        
        logger.info(f"Processing word: {word}, game_type: {game_type}")
        
        try:
            if game_type == 'multiple_choice_spelling':
                game_data = generate_multiple_choice_spelling(word)
            elif game_type == 'suffix_completion':
                game_data = generate_suffix_completion(word)
            elif game_type == 'fill_blanks':
                game_data = generate_fill_blanks(word)
            elif game_type == 'error_detection':
                game_data = generate_error_detection(word)
            elif game_type == 'guided_completion':
                game_data = generate_guided_completion(word)
            else:
                logger.warning(f"Unknown game type: {game_type}")
                continue
            
            results.append({
                'word': word,
                'game_type': game_type,
                'game_data': game_data
            })
            
            logger.info(f"Successfully generated {game_type} for word: {word}")
            
        except Exception as e:
            logger.error(f"Error generating game for word '{word}': {e}")
            continue
    
    logger.info(f"Successfully generated {len(results)} games")
    return jsonify({'results': results})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'groq_api_key_configured': bool(GROQ_API_KEY)
    })

@app.route('/api/test-groq', methods=['GET'])
def test_groq():
    """Test endpoint to check Groq API connection"""
    if not GROQ_API_KEY:
        return jsonify({'error': 'GROQ_API_KEY not configured'}), 500
    
    test_response = call_groq_api("Say 'Hello, this is a test!'")
    
    if test_response:
        return jsonify({
            'status': 'success',
            'message': 'Groq API is working',
            'response': test_response
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to connect to Groq API'
        }), 500

if __name__ == '__main__':
    print(f"GROQ_API_KEY configured: {bool(GROQ_API_KEY)}")
    app.run(debug=True, port=5000)
