import React, { useState } from 'react';
import { Upload, Play, Trash2, Plus, RefreshCw } from 'lucide-react';

const GAME_TYPES = [
  { value: 'multiple_choice_spelling', label: 'Multiple Choice Spelling Challenge' },
  { value: 'suffix_completion', label: 'Suffix Completion' },
  { value: 'fill_blanks', label: 'Fill in the Blanks' },
  { value: 'error_detection', label: 'Error Detection' },
  { value: 'guided_completion', label: 'Guided Word Completion' }
];

// Real API configuration
const API_BASE_URL = 'https://ai-game-backend.onrender.com'; // Change this to your actual backend URL

// Real API function to generate all games
const generateGames = async (words) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-all-games`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        words: words
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Function to generate a single game (if needed)
const generateSingleGame = async (word, gameType) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-game`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        word: word,
        game_type: gameType
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

function App() {
  const [words, setWords] = useState([
    { id: 1, word: '', gameType: 'multiple_choice_spelling' }
  ]);
  const [gameResults, setGameResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const addWordSlot = () => {
    if (words.length < 10) {
      const newId = Math.max(...words.map(w => w.id), 0) + 1;
      setWords([...words, { id: newId, word: '', gameType: 'multiple_choice_spelling' }]);
    }
  };

  const removeWordSlot = (id) => {
    if (words.length > 1) {
      setWords(words.filter(w => w.id !== id));
    }
  };

  const updateWord = (id, field, value) => {
    setWords(words.map(w => w.id === id ? { ...w, [field]: value } : w));
  };

  const generateAllGames = async () => {
    const validWords = words.filter(w => w.word.trim());
    
    if (validWords.length === 0) {
      setError('Please enter at least one word');
      return;
    }

    setIsLoading(true);
    setError('');
    setGameResults([]);

    try {
      // Make real API call
      const data = await generateGames(validWords.map(w => ({
        word: w.word.trim(),
        game_type: w.gameType
      })));
      
      if (data.results && data.results.length > 0) {
        setGameResults(data.results);
      } else {
        setError('No games were generated. Please check your words and try again.');
      }
    } catch (error) {
      console.error('Error generating games:', error);
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        setError('Unable to connect to the server. Please make sure the backend is running on http://localhost:5000');
      } else {
        setError(`Failed to generate games: ${error.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const GameResultCard = ({ result }) => {
    const { word, game_type, game_data } = result;
    
    const renderGameContent = () => {
      switch (game_type) {
        case 'multiple_choice_spelling':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-base">Choose the correct spelling:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-3 rounded-lg border-2 text-left transition-all duration-200 font-medium ${
                      option === game_data.correct
                        ? 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          );

        case 'suffix_completion':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-sm sm:text-base">Complete the word:</p>
              <div className="text-xl sm:text-2xl font-bold text-center py-4 sm:py-6 bg-blue-100 border-2 border-blue-200 rounded-lg text-blue-900">
                {game_data.base_word}<span className="text-blue-600">____</span>
              </div>
              <div className="grid grid-cols-1 gap-2 sm:gap-3">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-2 sm:p-3 rounded-lg border-2 text-center transition-all duration-200 font-medium text-sm sm:text-base ${
                      option === game_data.correct_suffix
                        ? 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          );

        case 'fill_blanks':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-sm sm:text-base">Fill in the missing letters:</p>
              <div className="text-xl sm:text-2xl font-bold text-center py-4 sm:py-6 bg-yellow-100 border-2 border-yellow-200 rounded-lg text-yellow-900">
                {game_data.blanked_word}
              </div>
              <div className="grid grid-cols-1 gap-2 sm:gap-3">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-2 sm:p-3 rounded-lg border-2 text-center transition-all duration-200 font-medium text-sm sm:text-base ${
                      option === game_data.correct_answer
                        ? 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          );

        case 'error_detection':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-sm sm:text-base">Find the error in this word:</p>
              <div className="text-xl sm:text-2xl font-bold text-center py-4 sm:py-6 bg-red-100 border-2 border-red-300 border-dashed rounded-lg text-red-800">
                {game_data.misspelled_word}
              </div>
              <div className="bg-gray-100 border border-gray-300 p-3 sm:p-4 rounded-lg">
                <p className="text-gray-800 font-medium text-sm sm:text-base">
                  <span className="text-gray-700">Correct spelling:</span> 
                  <span className="font-bold text-green-800 ml-2">{game_data.original_word}</span>
                </p>
              </div>
            </div>
          );

        case 'guided_completion':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-sm sm:text-base">Complete the word using the hint:</p>
              <div className="text-xl sm:text-2xl font-bold text-center py-4 sm:py-6 bg-purple-100 border-2 border-purple-200 rounded-lg text-purple-900">
                {game_data.incomplete_word}
              </div>
              <div className="bg-blue-100 border border-blue-300 p-3 sm:p-4 rounded-lg">
                <p className="font-semibold text-blue-900 mb-1 text-sm sm:text-base">Hint:</p>
                <p className="text-blue-800 font-medium text-sm sm:text-base">{game_data.hint}</p>
              </div>
              <div className="bg-gray-100 border border-gray-300 p-3 sm:p-4 rounded-lg">
                <p className="text-gray-800 font-medium text-sm sm:text-base">
                  <span className="text-gray-700">Answer:</span> 
                  <span className="font-bold text-green-800 ml-2">{game_data.correct_completion}</span>
                </p>
              </div>
            </div>
          );

        default:
          return <p className="text-gray-600 font-medium">Unknown game type</p>;
      }
    };

    return (
      <div className="bg-white rounded-lg sm:rounded-xl shadow-lg p-4 sm:p-6 border border-gray-200 hover:shadow-xl transition-shadow duration-300 w-full">
        <div className="flex flex-col gap-3 sm:gap-0 sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6">
          <h3 className="text-lg sm:text-xl font-bold text-gray-800">
            Word: <span className="text-blue-600">"{word}"</span>
          </h3>
          <span className="px-3 py-2 bg-blue-600 text-white rounded-lg text-xs sm:text-sm font-medium self-start sm:self-auto">
            {GAME_TYPES.find(gt => gt.value === game_type)?.label || game_type}
          </span>
        </div>
        <div className="w-full">
          {renderGameContent()}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 to-indigo-100 py-4 sm:py-6 px-2 sm:px-4">
      <div className="w-full max-w-none xl:max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8 px-2">
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-gray-800 mb-2 sm:mb-3">
            Word Learning Games Platform
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-700 max-w-full sm:max-w-2xl mx-auto px-2">
            Create interactive learning games for up to 10 words
          </p>
        </div>

         


        {/* Word Input Section */}
        <div className="bg-white rounded-lg sm:rounded-xl shadow-lg p-4 sm:p-6 mb-6 sm:mb-8 border border-gray-200 mx-2 sm:mx-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 gap-3 sm:gap-4">
            <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-800">
              Upload Words & Assign Games
            </h2>
            <button
              onClick={addWordSlot}
              disabled={words.length >= 10}
              className="flex items-center justify-center gap-2 px-3 sm:px-4 py-2 sm:py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium text-sm sm:text-base w-full sm:w-auto"
            >
              <Plus size={16} className="sm:hidden" />
              <Plus size={18} className="hidden sm:block" />
              Add Word ({words.length}/10)
            </button>
          </div>

          <div className="space-y-3 sm:space-y-4">
            {words.map((wordItem) => (
              <div key={wordItem.id} className="flex flex-col gap-3 p-3 sm:p-4 border-2 border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Enter a word..."
                      value={wordItem.word}
                      onChange={(e) => updateWord(wordItem.id, 'word', e.target.value)}
                      className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-800 font-medium text-sm sm:text-base"
                    />
                  </div>
                  <div className="flex-1">
                    <select
                      value={wordItem.gameType}
                      onChange={(e) => updateWord(wordItem.id, 'gameType', e.target.value)}
                      className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-800 font-medium text-sm sm:text-base"
                    >
                      {GAME_TYPES.map((gameType) => (
                        <option key={gameType.value} value={gameType.value}>
                          {gameType.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => removeWordSlot(wordItem.id)}
                    disabled={words.length <= 1}
                    className="p-2 sm:p-3 text-red-600 hover:bg-red-50 border-2 border-red-200 hover:border-red-300 rounded-lg disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    <Trash2 size={16} className="sm:hidden" />
                    <Trash2 size={18} className="hidden sm:block" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center mt-6 sm:mt-8">
            <button
              onClick={generateAllGames}
              disabled={isLoading || words.every(w => !w.word.trim())}
              className="flex items-center justify-center gap-2 sm:gap-3 px-6 sm:px-8 py-3 sm:py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-bold text-base sm:text-lg shadow-lg hover:shadow-xl w-full sm:w-auto max-w-xs sm:max-w-none"
            >
              {isLoading ? (
                <RefreshCw size={20} className="animate-spin sm:hidden" />
              ) : (
                <Play size={20} className="sm:hidden" />
              )}
              {isLoading ? (
                <RefreshCw size={24} className="animate-spin hidden sm:block" />
              ) : (
                <Play size={24} className="hidden sm:block" />
              )}
              {isLoading ? 'Generating Games...' : 'Generate All Games'}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border-2 border-red-300 text-red-800 px-4 sm:px-6 py-3 sm:py-4 rounded-lg mb-6 sm:mb-8 font-medium mx-2 sm:mx-0">
            <p className="font-bold text-sm sm:text-base">Error:</p>
            <p className="text-sm sm:text-base">{error}</p>
            {error.includes('connect to the server') && (
              <div className="mt-2 text-sm">
                <p className="font-semibold">Troubleshooting steps:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Make sure your Flask backend is running: <code className="bg-red-200 px-1 rounded">python app.py</code></li>
                  <li>Verify the backend is accessible at: <code className="bg-red-200 px-1 rounded">{API_BASE_URL}</code></li>
                  <li>Check that CORS is properly configured in your Flask app</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Game Results Section */}
        {gameResults.length > 0 && (
          <div className="px-2 sm:px-0">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-800 mb-6 sm:mb-8 text-center">
              Generated Games ({gameResults.length})
            </h2>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
              {gameResults.map((result, index) => (
                <GameResultCard key={index} result={result} />
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {gameResults.length === 0 && !isLoading && (
          <div className="bg-white border-2 border-blue-200 rounded-lg sm:rounded-xl p-6 sm:p-8 text-center shadow-lg mx-2 sm:mx-0">
            <Upload size={48} className="mx-auto text-blue-500 mb-4 sm:hidden" />
            <Upload size={64} className="mx-auto text-blue-500 mb-6 hidden sm:block" />
            <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-blue-800 mb-3 sm:mb-4">
              Ready to Create Learning Games!
            </h3>
            <p className="text-blue-700 text-base sm:text-lg font-medium max-w-full sm:max-w-xl mx-auto">
              Enter your words, select game types, and click "Generate All Games" to create interactive learning experiences.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;