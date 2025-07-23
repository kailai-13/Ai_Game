from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import os
from typing import Dict, List, Any
import logging

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
        'model': 'llama3-8b-8192',  # Updated to a valid Groq model
        'temperature': 0.3,  # Reduced temperature for more consistent output
        'max_tokens': 500,   # Reduced tokens to avoid issues
        'top_p': 1.0,
        'stream': False
    }
    
    try:
        logger.info(f"Making request to Groq API with model: {data['model']}")
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        
        # Log the response status and content for debugging
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
    """Generate multiple choice spelling challenge"""
    prompt = f"""Create a multiple choice spelling challenge for the word "{word}".

Generate 3 believable misspellings and include the correct spelling.

Respond with ONLY valid JSON in this exact format:
{{
    "correct": "{word}",
    "options": ["correct_spelling", "misspelling1", "misspelling2", "misspelling3"]
}}

Do not include any other text or explanations."""
    
    response = call_groq_api(prompt)
    if response:
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for word '{word}': {e}")
            logger.error(f"Response was: {response}")
    
    # Enhanced fallback
    return {
        "correct": word,
        "options": [word, word.replace('e', 'i'), word + 'e', word.replace('a', 'e')][:4]
    }

def generate_suffix_completion(word: str) -> Dict[str, Any]:
    """Generate suffix completion challenge"""
    if len(word) <= 4:
        base_word = word[:-2] if len(word) > 2 else word[:-1]
    else:
        base_word = word[:-3]
    
    correct_suffix = word[len(base_word):]
    
    prompt = f"""Create a suffix completion challenge for the word "{word}".
The base word is "{base_word}" and the correct suffix is "{correct_suffix}".

Generate 3 plausible but incorrect suffix options.

Respond with ONLY valid JSON in this exact format:
{{
    "base_word": "{base_word}",
    "correct_suffix": "{correct_suffix}",
    "options": ["correct_suffix", "wrong_suffix1", "wrong_suffix2", "wrong_suffix3"]
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
            logger.error(f"JSON decode error for suffix completion '{word}': {e}")
    
    # Fallback
    return {
        "base_word": base_word,
        "correct_suffix": correct_suffix,
        "options": [correct_suffix, "ing", "ed", "er"][:4]
    }

def generate_fill_blanks(word: str) -> Dict[str, Any]:
    """Generate fill in the blanks challenge"""
    import random
    
    # Create blanked word
    word_list = list(word)
    num_blanks = min(2, len(word) - 1)
    positions_to_replace = random.sample(range(len(word)), num_blanks)
    
    blanked_word = ""
    for i, letter in enumerate(word_list):
        if i in positions_to_replace:
            blanked_word += "_"
        else:
            blanked_word += letter
    
    prompt = f"""Create a fill-in-the-blanks challenge for the word "{word}".
The blanked version is "{blanked_word}".

Generate 3 incorrect options that could plausibly fill the blanks.

Respond with ONLY valid JSON in this exact format:
{{
    "blanked_word": "{blanked_word}",
    "correct_answer": "{word}",
    "options": ["{word}", "wrong_option1", "wrong_option2", "wrong_option3"]
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
            logger.error(f"JSON decode error for fill blanks '{word}': {e}")
    
    # Fallback
    return {
        "blanked_word": blanked_word,
        "correct_answer": word,
        "options": [word, word + "s", word.replace(word[-1], "x"), word[:-1] + "y"][:4]
    }

def generate_error_detection(word: str) -> Dict[str, Any]:
    """Generate error detection challenge"""
    prompt = f"""Create an error detection challenge for the word "{word}".

Generate one believable misspelling that users need to identify as incorrect.

Respond with ONLY valid JSON in this exact format:
{{
    "original_word": "{word}",
    "misspelled_word": "misspelled_version"
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
    incomplete_length = max(1, len(word) - 2)
    incomplete_word = word[:incomplete_length] + "_" * (len(word) - incomplete_length)
    
    prompt = f"""Create a guided word completion challenge for the word "{word}".
The incomplete word is "{incomplete_word}".

Provide a helpful hint about the word's meaning or usage.

Respond with ONLY valid JSON in this exact format:
{{
    "incomplete_word": "{incomplete_word}",
    "hint": "helpful hint about the word",
    "correct_completion": "{word}"
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
            logger.error(f"JSON decode error for guided completion '{word}': {e}")
    
    # Fallback
    return {
        "incomplete_word": incomplete_word,
        "hint": f"This word has {len(word)} letters and ends with '{word[-2:]}'",
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