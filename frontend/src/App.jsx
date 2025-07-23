import React, { useState } from 'react';
import { Upload, Play, Trash2, Plus, RefreshCw } from 'lucide-react';

const GAME_TYPES = [
  { value: 'multiple_choice_spelling', label: 'Multiple Choice Spelling Challenge' },
  { value: 'suffix_completion', label: 'Suffix Completion' },
  { value: 'fill_blanks', label: 'Fill in the Blanks' },
  { value: 'error_detection', label: 'Error Detection' },
  { value: 'guided_completion', label: 'Guided Word Completion' }
];

// Mock API function for demo purposes (since localhost API won't work in artifacts)
const mockGenerateGames = async (words) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  return {
    results: words.map(wordItem => {
      const { word, game_type } = wordItem;
      
      switch (game_type) {
        case 'multiple_choice_spelling':
          return {
            word,
            game_type,
            game_data: {
              options: [word, word.slice(0, -1) + 'x', word.slice(0, -2) + 'yz', word + 's'],
              correct: word
            }
          };
          
        case 'suffix_completion':
          const baseWord = word.slice(0, Math.max(3, word.length - 3));
          const suffix = word.slice(baseWord.length);
          return {
            word,
            game_type,
            game_data: {
              base_word: baseWord,
              options: [suffix, suffix + 'x', 'ing', 'ed'],
              correct_suffix: suffix
            }
          };
          
        case 'fill_blanks':
          const blankedWord = word.split('').map((char, i) => 
            i === Math.floor(word.length / 2) || i === Math.floor(word.length / 3) ? '_' : char
          ).join('');
          return {
            word,
            game_type,
            game_data: {
              blanked_word: blankedWord,
              options: [word, word.slice(0, -1) + 'x', word + 'y', word.slice(1)],
              correct_answer: word
            }
          };
          
        case 'error_detection':
          const misspelled = word.slice(0, -1) + (word.slice(-1) === 'e' ? 'a' : 'e');
          return {
            word,
            game_type,
            game_data: {
              misspelled_word: misspelled,
              original_word: word
            }
          };
          
        case 'guided_completion':
          const incomplete = word.slice(0, -2) + '__';
          return {
            word,
            game_type,
            game_data: {
              incomplete_word: incomplete,
              hint: `This word ends with "${word.slice(-2)}"`,
              correct_completion: word
            }
          };
          
        default:
          return { word, game_type, game_data: {} };
      }
    })
  };
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
      // Using mock API for demo
      const data = await mockGenerateGames(validWords.map(w => ({
        word: w.word.trim(),
        game_type: w.gameType
      })));
      
      setGameResults(data.results || []);
    } catch (error) {
      console.error('Error generating games:', error);
      setError('Failed to generate games. Please try again.');
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
              <p className="font-semibold text-gray-800 text-base">Complete the word:</p>
              <div className="text-2xl font-bold text-center py-6 bg-blue-100 border-2 border-blue-200 rounded-lg text-blue-900">
                {game_data.base_word}<span className="text-blue-600">____</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-3 rounded-lg border-2 text-center transition-all duration-200 font-medium ${
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
              <p className="font-semibold text-gray-800 text-base">Fill in the missing letters:</p>
              <div className="text-2xl font-bold text-center py-6 bg-yellow-100 border-2 border-yellow-200 rounded-lg text-yellow-900">
                {game_data.blanked_word}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {game_data.options?.map((option, index) => (
                  <button
                    key={index}
                    className={`p-3 rounded-lg border-2 text-center transition-all duration-200 font-medium ${
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
              <p className="font-semibold text-gray-800 text-base">Find the error in this word:</p>
              <div className="text-2xl font-bold text-center py-6 bg-red-100 border-2 border-red-300 border-dashed rounded-lg text-red-800">
                {game_data.misspelled_word}
              </div>
              <div className="bg-gray-100 border border-gray-300 p-4 rounded-lg">
                <p className="text-gray-800 font-medium">
                  <span className="text-gray-700">Correct spelling:</span> 
                  <span className="font-bold text-green-800 ml-2">{game_data.original_word}</span>
                </p>
              </div>
            </div>
          );

        case 'guided_completion':
          return (
            <div className="space-y-4">
              <p className="font-semibold text-gray-800 text-base">Complete the word using the hint:</p>
              <div className="text-2xl font-bold text-center py-6 bg-purple-100 border-2 border-purple-200 rounded-lg text-purple-900">
                {game_data.incomplete_word}
              </div>
              <div className="bg-blue-100 border border-blue-300 p-4 rounded-lg">
                <p className="font-semibold text-blue-900 mb-1">Hint:</p>
                <p className="text-blue-800 font-medium">{game_data.hint}</p>
              </div>
              <div className="bg-gray-100 border border-gray-300 p-4 rounded-lg">
                <p className="text-gray-800 font-medium">
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
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-shadow duration-300">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-3">
          <h3 className="text-xl font-bold text-gray-800">
            Word: <span className="text-blue-600">"{word}"</span>
          </h3>
          <span className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium self-start sm:self-auto">
            {GAME_TYPES.find(gt => gt.value === game_type)?.label || game_type}
          </span>
        </div>
        {renderGameContent()}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-6 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-800 mb-3">
            Word Learning Games Platform
          </h1>
          <p className="text-lg md:text-xl text-gray-700 max-w-2xl mx-auto">
            Create interactive learning games for up to 10 words
          </p>
        </div>

        {/* Word Input Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
            <h2 className="text-xl md:text-2xl font-bold text-gray-800">
              Upload Words & Assign Games
            </h2>
            <button
              onClick={addWordSlot}
              disabled={words.length >= 10}
              className="flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium self-start sm:self-auto"
            >
              <Plus size={18} />
              Add Word ({words.length}/10)
            </button>
          </div>

          <div className="space-y-4">
            {words.map((wordItem) => (
              <div key={wordItem.id} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 p-4 border-2 border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Enter a word..."
                    value={wordItem.word}
                    onChange={(e) => updateWord(wordItem.id, 'word', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-800 font-medium"
                  />
                </div>
                <div className="flex-1">
                  <select
                    value={wordItem.gameType}
                    onChange={(e) => updateWord(wordItem.id, 'gameType', e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-800 font-medium"
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
                  className="p-3 text-red-600 hover:bg-red-50 border-2 border-red-200 hover:border-red-300 rounded-lg disabled:text-gray-400 disabled:border-gray-200 disabled:cursor-not-allowed transition-all duration-200 self-start sm:self-auto"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-center mt-8">
            <button
              onClick={generateAllGames}
              disabled={isLoading || words.every(w => !w.word.trim())}
              className="flex items-center gap-3 px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-bold text-lg shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <RefreshCw size={24} className="animate-spin" />
              ) : (
                <Play size={24} />
              )}
              {isLoading ? 'Generating Games...' : 'Generate All Games'}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border-2 border-red-300 text-red-800 px-6 py-4 rounded-lg mb-8 font-medium">
            <p className="font-bold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Game Results Section */}
        {gameResults.length > 0 && (
          <div>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-800 mb-8 text-center">
              Generated Games ({gameResults.length})
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {gameResults.map((result, index) => (
                <GameResultCard key={index} result={result} />
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {gameResults.length === 0 && !isLoading && (
          <div className="bg-white border-2 border-blue-200 rounded-xl p-8 text-center shadow-lg">
            <Upload size={64} className="mx-auto text-blue-500 mb-6" />
            <h3 className="text-xl md:text-2xl font-bold text-blue-800 mb-4">
              Ready to Create Learning Games!
            </h3>
            <p className="text-blue-700 text-lg font-medium max-w-xl mx-auto">
              Enter your words, select game types, and click "Generate All Games" to create interactive learning experiences.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;