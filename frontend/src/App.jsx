import React, { useState } from 'react';
import { Upload, Play, Trash2, Plus, RefreshCw } from 'lucide-react';

const GAME_TYPES = [
  { value: 'multiple_choice_spelling', label: 'Multiple Choice Spelling Challenge' },
  { value: 'suffix_completion', label: 'Suffix Completion' },
  { value: 'fill_blanks', label: 'Fill in the Blanks' },
  { value: 'error_detection', label: 'Error Detection' },
  { value: 'guided_completion', label: 'Guided Word Completion' }
];

const API_BASE_URL = 'http://localhost:5000/api';

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
      const response = await fetch(`${API_BASE_URL}/generate-all-games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          words: validWords.map(w => ({
            word: w.word.trim(),
            game_type: w.gameType
          }))
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setGameResults(data.results || []);
    } catch (error) {
      console.error('Error generating games:', error);
      setError('Failed to generate games. Please check if the backend server is running.');
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
            <div className="space-y-3">
              <p className="font-medium text-gray-700">Choose the correct spelling:</p>
              <div className="grid grid-cols-2 gap-2">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-2 rounded border text-left transition-colors ${
                      option === game_data.correct
                        ? 'bg-green-50 border-green-200 hover:bg-green-100'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
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
            <div className="space-y-3">
              <p className="font-medium text-gray-700">Complete the word:</p>
              <div className="text-2xl font-bold text-center py-4 bg-blue-50 rounded">
                {game_data.base_word}<span className="text-blue-600">____</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-2 rounded border text-center transition-colors ${
                      option === game_data.correct_suffix
                        ? 'bg-green-50 border-green-200 hover:bg-green-100'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
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
            <div className="space-y-3">
              <p className="font-medium text-gray-700">Fill in the missing letters:</p>
              <div className="text-2xl font-bold text-center py-4 bg-yellow-50 rounded">
                {game_data.blanked_word}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-2 rounded border text-center transition-colors ${
                      option === game_data.correct_answer
                        ? 'bg-green-50 border-green-200 hover:bg-green-100'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
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
            <div className="space-y-3">
              <p className="font-medium text-gray-700">Find the error in this word:</p>
              <div className="text-2xl font-bold text-center py-4 bg-red-50 rounded border-2 border-dashed border-red-200">
                {game_data.misspelled_word}
              </div>
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                <strong>Correct spelling:</strong> {game_data.original_word}
              </div>
            </div>
          );

        case 'guided_completion':
          return (
            <div className="space-y-3">
              <p className="font-medium text-gray-700">Complete the word using the hint:</p>
              <div className="text-2xl font-bold text-center py-4 bg-purple-50 rounded">
                {game_data.incomplete_word}
              </div>
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm font-medium text-blue-800">Hint:</p>
                <p className="text-blue-700">{game_data.hint}</p>
              </div>
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                <strong>Answer:</strong> {game_data.correct_completion}
              </div>
            </div>
          );

        default:
          return <p className="text-gray-500">Unknown game type</p>;
      }
    };

    return (
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-800 capitalize">
            Word: "{word}"
          </h3>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
            {GAME_TYPES.find(gt => gt.value === game_type)?.label || game_type}
          </span>
        </div>
        {renderGameContent()}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Word Learning Games Platform
          </h1>
          <p className="text-lg text-gray-600">
            Create interactive learning games for up to 10 words
          </p>
        </div>

        {/* Word Input Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              Upload Words & Assign Games
            </h2>
            <button
              onClick={addWordSlot}
              disabled={words.length >= 10}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <Plus size={16} />
              Add Word ({words.length}/10)
            </button>
          </div>

          <div className="space-y-4">
            {words.map((wordItem) => (
              <div key={wordItem.id} className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Enter a word..."
                    value={wordItem.word}
                    onChange={(e) => updateWord(wordItem.id, 'word', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex-1">
                  <select
                    value={wordItem.gameType}
                    onChange={(e) => updateWord(wordItem.id, 'gameType', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {GAME_TYPES.map((gameType) => (
                      <option key={gameType.value} value={gameType.value}>
                        {gameType.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={() => removeWordSlot(wordItem.id)}
                  disabled={words.length <= 1}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-md disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-center mt-6">
            <button
              onClick={generateAllGames}
              disabled={isLoading || words.every(w => !w.word.trim())}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isLoading ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                <Play size={20} />
              )}
              {isLoading ? 'Generating Games...' : 'Generate All Games'}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Game Results Section */}
        {gameResults.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
              Generated Games ({gameResults.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {gameResults.map((result, index) => (
                <GameResultCard key={index} result={result} />
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {gameResults.length === 0 && !isLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <Upload size={48} className="mx-auto text-blue-400 mb-4" />
            <h3 className="text-lg font-medium text-blue-800 mb-2">
              Ready to Create Learning Games!
            </h3>
            <p className="text-blue-600">
              Enter your words, select game types, and click "Generate All Games" to create interactive learning experiences.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;