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

def create_human_like_misspellings(word: str) -> List[str]:
    """Create realistic human-like misspellings"""
    misspellings = []
    word_lower = word.lower()
    
    # Common letter swaps
    common_swaps = [('ie', 'ei'), ('ei', 'ie'), ('ph', 'f'), ('gh', 'g'), ('ck', 'k')]
    for original, replacement in common_swaps:
        if original in word_lower:
            misspelling = word_lower.replace(original, replacement, 1)
            if misspelling != word_lower:
                misspellings.append(misspelling)
    
    # Double letter mistakes
    for i in range(len(word_lower) - 1):
        if word_lower[i] == word_lower[i + 1]:  # Remove double letter
            misspelling = word_lower[:i] + word_lower[i + 1:]
            misspellings.append(misspelling)
        else:  # Add double letter
            misspelling = word_lower[:i + 1] + word_lower[i] + word_lower[i + 1:]
            misspellings.append(misspelling)
    
    # Silent letter removal
    silent_patterns = ['k', 'b', 'w', 'h', 'l', 't']
    for letter in silent_patterns:
        if letter in word_lower:
            misspelling = word_lower.replace(letter, '', 1)
            if len(misspelling) >= 3 and misspelling != word_lower:
                misspellings.append(misspelling)
    
    # Vowel confusion
    vowel_swaps = [('a', 'e'), ('e', 'i'), ('i', 'o'), ('o', 'u'), ('u', 'a')]
    for original, replacement in vowel_swaps:
        if original in word_lower:
            misspelling = word_lower.replace(original, replacement, 1)
            if misspelling != word_lower:
                misspellings.append(misspelling)
    
    # Phonetic mistakes
    phonetic_swaps = [('c', 'k'), ('s', 'c'), ('f', 'ph'), ('j', 'g')]
    for original, replacement in phonetic_swaps:
        if original in word_lower:
            misspelling = word_lower.replace(original, replacement, 1)
            if misspelling != word_lower:
                misspellings.append(misspelling)
    
    # Return unique misspellings, limit to avoid too many options
    unique_misspellings = list(set(misspellings))
    return unique_misspellings[:6]  # Return up to 6 options

def generate_multiple_choice_spelling(word: str) -> Dict[str, Any]:
    """Generate multiple choice spelling challenge with human-like mistakes"""
    prompt = f"""Create a multiple choice spelling challenge for the word "{word}".

Generate 3 realistic misspellings that humans commonly make. Focus on:
- Common letter confusions (ei/ie, ph/f, c/k, s/c)
- Double letter mistakes (adding or removing doubles)
- Silent letter errors
- Vowel confusions
- Phonetic mistakes

Make the mistakes subtle and tempting - they should look plausible.

Respond with ONLY valid JSON in this exact format:
{{
    "correct": "{word}",
    "options": ["correct_spelling", "realistic_misspelling1", "realistic_misspelling2", "realistic_misspelling3"]
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

    # Enhanced fallback with human-like mistakes
    misspellings = create_human_like_misspellings(word)
    options = [word] + misspellings[:3]
    
    # If we don't have enough misspellings, add some generic ones
    while len(options) < 4:
        if len(word) > 3:
            # Add common suffix confusion
            if word.endswith('tion'):
                options.append(word.replace('tion', 'sion'))
            elif word.endswith('able'):
                options.append(word.replace('able', 'ible'))
            elif 'ei' in word:
                options.append(word.replace('ei', 'ie'))
            else:
                # Generic letter swap
                pos = random.randint(1, len(word) - 2)
                generic_mistake = word[:pos] + word[pos+1] + word[pos] + word[pos+2:]
                options.append(generic_mistake)
        else:
            options.append(word + random.choice(['e', 's', 'ed']))
    
    # Shuffle options but keep track of correct answer
    random.shuffle(options)
    
    return {
        "correct": word,
        "options": options[:4]
    }

def generate_suffix_completion(word: str) -> Dict[str, Any]:
    """Generate suffix completion challenge with tempting, human-like suffixes"""
    if len(word) <= 4:
        base_word = word[:-2] if len(word) > 2 else word[:-1]
    else:
        base_word = word[:-3]

    correct_suffix = word[len(base_word):]

    prompt = f"""You are a language tutor.

Create a suffix-completion challenge for the word "{word}".
The base word is "{base_word}" and the correct suffix is "{correct_suffix}".

Generate 3 **tempting but wrong** suffixes that:
- Are real suffixes used in English
- Are commonly confused in spelling (-tion vs -sion, -able vs -ible, etc.)
- Are close in sound or appearance to the correct one
- Could realistically complete the base word, but are wrong

✅ Output only valid JSON in this format:
{{
    "base_word": "{base_word}",
    "correct_suffix": "{correct_suffix}",
    "options": ["{correct_suffix}", "wrong_suffix1", "wrong_suffix2", "wrong_suffix3"]
}}

No explanations. No extra text. Only JSON."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
            
            result = json.loads(cleaned_response)
            result['options'] = [suffix.strip() for suffix in result['options']]
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for suffix completion '{word}': {e}")
            logger.error(f"Response was: {response}")

    # 🧠 Better fallback logic
    fallback_map = {
        'tion': ['sion', 'cion', 'tian'],
        'sion': ['tion', 'ssion', 'cion'],
        'able': ['ible', 'eable', 'uble'],
        'ible': ['able', 'eable', 'uble'],
        'ous': ['ious', 'eous', 'us'],
        'ious': ['ous', 'eous', 'iouss'],
        'ant': ['ent', 'int', 'unt'],
        'ent': ['ant', 'int', 'end'],
        'ive': ['ative', 'ivee', 'eive'],
        'al': ['el', 'le', 'il'],
    }

    correct_suffix_lower = correct_suffix.lower()
    confusing_suffixes = fallback_map.get(correct_suffix_lower, ['ing', 'er', 'ly', 'est', 'ment'])

    # Ensure no duplicates and correct_suffix is not included in wrong ones
    confusing_suffixes = [s for s in confusing_suffixes if s != correct_suffix_lower][:3]

    while len(confusing_suffixes) < 3:
        extra = random.choice(['ence', 'ance', 'ary', 'ory', 'ive', 'ure'])
        if extra not in confusing_suffixes and extra != correct_suffix_lower:
            confusing_suffixes.append(extra)

    options = [correct_suffix] + confusing_suffixes[:3]
    random.shuffle(options)

    return {
        "base_word": base_word,
        "correct_suffix": correct_suffix,
        "options": options[:4]
    }



def generate_fill_blanks(word: str) -> Dict[str, Any]:
    """Generate fill-in-the-blanks challenge with realistic and tempting wrong 2-letter combinations"""
    if len(word) < 3:
        return {
            "blanked_word": word,
            "correct_answer": word,
            "missing_letters": word[-1:],
            "options": [word[-1:], "s", "e", "d"]
        }

    problem_patterns = ['ie', 'ei', 'ou', 'ea', 'oo', 'ee', 'ss', 'll', 'nn', 'mm', 'tt']
    best_position = 0
    for pattern in problem_patterns:
        pos = word.lower().find(pattern)
        if pos != -1 and pos + 2 <= len(word):
            best_position = pos
            break
    if best_position == 0:
        best_position = random.randint(1, len(word) - 3) if len(word) >= 4 else 0

    blanked_word = word[:best_position] + "__" + word[best_position + 2:]
    missing_letters = word[best_position:best_position + 2].lower()

    prompt = f"""Create a fill-in-the-blanks challenge for the word "{word}".
The blanked version is "{blanked_word}" and the missing letters are "{missing_letters}".

Generate 3 wrong but very tempting 2-letter combinations:
- Use phonetically or visually confusing pairs
- Include real English letter pairs that are common in the same position
- Include commonly mistaken spellings
- Do NOT include nonsense combinations

Respond with only valid JSON:
{{
    "blanked_word": "{blanked_word}",
    "correct_answer": "{word}",
    "missing_letters": "{missing_letters}",
    "options": ["{missing_letters}", "wrong_combo1", "wrong_combo2", "wrong_combo3"]
}}"""

    response = call_groq_api(prompt)
    if response:
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(cleaned_response)
            result['options'] = [opt[:2] for opt in result['options'] if len(opt) >= 2]
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for fill blanks '{word}': {e}")

    # ✨ Better fallback with human-mistakable combos
    pairs_map = {
        'ie': ['ei', 'ea', 'ee'],
        'ei': ['ie', 'ai', 'ea'],
        'ou': ['ow', 'oo', 'au'],
        'ea': ['ee', 'ie', 'ai'],
        'oo': ['ou', 'ew', 'ue'],
        'ss': ['zz', 'll', 'sh'],
        'll': ['tt', 'ss', 'nn'],
        'mm': ['nn', 'rm', 'mn'],
        'tt': ['dd', 'll', 'pp'],
    }

    confusing_combos = pairs_map.get(missing_letters, [])

    while len(confusing_combos) < 3:
        extra = random.choice(['ai', 'ow', 'er', 'ar', 'en', 'on'])
        if extra not in confusing_combos and extra != missing_letters:
            confusing_combos.append(extra)

    options = [missing_letters] + confusing_combos[:3]
    random.shuffle(options)

    return {
        "blanked_word": blanked_word,
        "correct_answer": word,
        "missing_letters": missing_letters,
        "options": options[:4]
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
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
                
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for error detection '{word}': {e}")
    
    # Enhanced fallback with subtle mistakes
    word_lower = word.lower()
    
    # Try different types of subtle mistakes
    if 'ie' in word_lower:
        misspelled = word_lower.replace('ie', 'ei', 1)
    elif 'ei' in word_lower:
        misspelled = word_lower.replace('ei', 'ie', 1)
    elif len(word) > 4 and word_lower[-2:] in ['ed', 'er', 'ly']:
        # Double the last consonant before suffix
        base = word_lower[:-2]
        suffix = word_lower[-2:]
        if base and base[-1] not in 'aeiou':
            misspelled = base + base[-1] + suffix
        else:
            misspelled = word_lower.replace('e', 'i', 1)
    else:
        # Generic subtle mistake - swap adjacent letters
        if len(word) > 3:
            pos = len(word) // 2
            misspelled = word_lower[:pos] + word_lower[pos+1] + word_lower[pos] + word_lower[pos+2:]
        else:
            misspelled = word_lower.replace(word_lower[0], word_lower[0] + 'h', 1)
    
    return {
        "original_word": word,
        "misspelled_word": misspelled if misspelled != word_lower else word_lower + 'e'
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
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '')
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for guided completion '{word}': {e}")
            logger.error(f"Response was: {response}")

    
    # Enhanced fallback with better hints
    hints = [
        f"This {len(word)}-letter word starts with '{word[0]}' and ends with '{word[-1]}'",
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