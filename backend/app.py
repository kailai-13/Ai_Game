from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)

# Groq API configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'your-groq-api-key-here')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

def call_groq_api(prompt: str) -> str:
    """Call Groq API with the given prompt"""
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
        'model': 'mixtral-8x7b-32768',
        'temperature': 0.7,
        'max_tokens': 1024
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return ""

def generate_multiple_choice_spelling(word: str) -> Dict[str, Any]:
    """Generate multiple choice spelling challenge"""
    prompt = f"""
    Create a multiple choice spelling challenge for the word "{word}".
    Return ONLY a JSON object with this exact structure:
    {{
        "correct": "{word}",
        "options": ["correct_spelling", "misspelling1", "misspelling2", "misspelling3"]
    }}
    
    The options should include the correct spelling and 3 similar/commonly misspelled variants.
    Make sure the misspellings are believable but clearly wrong.
    """
    
    response = call_groq_api(prompt)
    try:
        return json.loads(response)
    except:
        # Fallback if API fails
        return {
            "correct": word,
            "options": [word, word.replace('e', 'i'), word + 'e', word.replace('a', 'e')]
        }

def generate_suffix_completion(word: str) -> Dict[str, Any]:
    """Generate suffix completion challenge"""
    if len(word) <= 4:
        base_word = word[:-2] if len(word) > 2 else word[:-1]
        suffix_length = len(word) - len(base_word)
    else:
        base_word = word[:-4]
        suffix_length = 4
    
    correct_suffix = word[len(base_word):]
    
    prompt = f"""
    Create a suffix completion challenge for the word "{word}".
    The base word is "{base_word}" and the correct suffix is "{correct_suffix}".
    Return ONLY a JSON object with this exact structure:
    {{
        "base_word": "{base_word}",
        "correct_suffix": "{correct_suffix}",
        "options": ["correct_suffix", "wrong_suffix1", "wrong_suffix2", "wrong_suffix3"]
    }}
    
    Create 3 plausible but incorrect suffix options.
    """
    
    response = call_groq_api(prompt)
    try:
        return json.loads(response)
    except:
        # Fallback
        return {
            "base_word": base_word,
            "correct_suffix": correct_suffix,
            "options": [correct_suffix, "ing", "ed", "er"]
        }

def generate_fill_blanks(word: str) -> Dict[str, Any]:
    """Generate fill in the blanks challenge"""
    # Replace 2-3 letters with dashes
    import random
    word_list = list(word)
    positions_to_replace = random.sample(range(len(word)), min(3, len(word) - 1))
    
    blanked_word = ""
    missing_letters = ""
    for i, letter in enumerate(word_list):
        if i in positions_to_replace:
            blanked_word += "_"
            missing_letters += letter
        else:
            blanked_word += letter
    
    prompt = f"""
    Create a fill-in-the-blanks challenge for the word "{word}".
    The blanked version is "{blanked_word}" and the missing letters are "{missing_letters}".
    Return ONLY a JSON object with this exact structure:
    {{
        "blanked_word": "{blanked_word}",
        "correct_answer": "{missing_letters}",
        "options": ["correct_letters", "wrong_letters1", "wrong_letters2", "wrong_letters3"]
    }}
    
    Create 3 plausible but incorrect letter combinations.
    """
    
    response = call_groq_api(prompt)
    try:
        return json.loads(response)
    except:
        # Fallback
        return {
            "blanked_word": blanked_word,
            "correct_answer": missing_letters,
            "options": [missing_letters, "abc", "xyz", "def"]
        }

def generate_error_detection(word: str) -> Dict[str, Any]:
    """Generate error detection challenge"""
    prompt = f"""
    Create an error detection challenge for the word "{word}".
    Return ONLY a JSON object with this exact structure:
    {{
        "original_word": "{word}",
        "misspelled_word": "intentionally_misspelled_version"
    }}
    
    Create one believable misspelling of the word that users need to identify as incorrect.
    """
    
    response = call_groq_api(prompt)
    try:
        return json.loads(response)
    except:
        # Fallback
        import random
        if len(word) > 3:
            pos = random.randint(1, len(word) - 2)
            misspelled = word[:pos] + 'x' + word[pos + 1:]
        else:
            misspelled = word + 'x'
        
        return {
            "original_word": word,
            "misspelled_word": misspelled
        }

def generate_guided_completion(word: str) -> Dict[str, Any]:
    """Generate guided word completion challenge"""
    # Create incomplete word (remove last few letters)
    incomplete_length = max(1, len(word) - 3)
    incomplete_word = word[:incomplete_length] + "_" * (len(word) - incomplete_length)
    
    prompt = f"""
    Create a guided word completion challenge for the word "{word}".
    The incomplete word is "{incomplete_word}".
    Return ONLY a JSON object with this exact structure:
    {{
        "incomplete_word": "{incomplete_word}",
        "hint": "contextual hint about the word",
        "correct_completion": "{word}"
    }}
    
    Provide a helpful hint that gives context about the word's meaning or usage.
    """
    
    response = call_groq_api(prompt)
    try:
        return json.loads(response)
    except:
        # Fallback
        return {
            "incomplete_word": incomplete_word,
            "hint": f"This word is commonly used and has {len(word)} letters total",
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
        return jsonify({'error': f'Failed to generate game: {str(e)}'}), 500

@app.route('/api/generate-all-games', methods=['POST'])
def generate_all_games():
    """Generate all games for a list of words with their assigned game types"""
    data = request.get_json()
    
    if not data or 'words' not in data:
        return jsonify({'error': 'Words array is required'}), 400
    
    words_data = data['words']
    results = []
    
    for word_item in words_data:
        if 'word' not in word_item or 'game_type' not in word_item:
            continue
            
        word = word_item['word'].strip().lower()
        game_type = word_item['game_type']
        
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
                continue
            
            results.append({
                'word': word,
                'game_type': game_type,
                'game_data': game_data
            })
        except Exception as e:
            print(f"Error generating game for word '{word}': {e}")
            continue
    
    return jsonify({'results': results})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)