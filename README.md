# Word Learning Games Platform

An interactive web application that generates various types of word learning games using AI. Teachers and educators can input words and automatically generate engaging spelling and vocabulary challenges for students.

## 🎯 Features

- **5 Different Game Types:**
  - Multiple Choice Spelling Challenge
  - Suffix Completion
  - Fill in the Blanks
  - Error Detection
  - Guided Word Completion

- **Batch Processing:** Generate games for up to 10 words simultaneously
- **AI-Powered:** Uses Groq API with Llama3 model for intelligent game generation
- **Responsive Design:** Works on desktop, tablet, and mobile devices
- **Real-time Generation:** Interactive interface with loading states and error handling

## 🏗️ Tech Stack

### Frontend
- **React** - User interface framework
- **Tailwind CSS** - Styling and responsive design
- **Lucide React** - Icon library
- **Fetch API** - HTTP client for API calls

### Backend
- **Flask** - Python web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Groq API** - AI model integration
- **Python-dotenv** - Environment variable management

## 📋 Prerequisites

Before running this application, make sure you have:

- **Node.js** (v14 or higher)
- **Python** (v3.8 or higher)
- **Groq API Key** - [Get one here](https://console.groq.com/)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kailai-13/Ai_Game
cd word-learning-games
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Create Environment File
Create a `.env` file in the backend directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

#### Install Required Packages
```bash
pip install flask flask-cors requests python-dotenv
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
# or
yarn install
```

## 🎮 Running the Application

### 1. Start the Backend Server
```bash
cd backend
python app.py
```
The Flask server will start on `http://localhost:5000`

### 2. Start the Frontend (Development)
```bash
cd frontend
npm start
# or
yarn start
```
The React app will start on `http://localhost:3000`

### 3. Access the Application
Open your browser and navigate to `http://localhost:3000`

## 🔧 Configuration

### Backend Configuration
- **Port:** Default is 5000, can be changed in `app.py`
- **Debug Mode:** Enabled by default for development
- **CORS:** Configured to allow all origins in development

### Frontend Configuration
- **API Base URL:** Configure in the React component (`API_BASE_URL` variable)
- **For production:** Update the API URL to your deployed backend

## 📝 API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### Health Check
```http
GET /health
```
Returns server status and API key configuration status.

#### Test Groq Connection
```http
GET /api/test-groq
```
Tests the connection to Groq API.

#### Generate Single Game
```http
POST /api/generate-game
```
**Request Body:**
```json
{
  "word": "example",
  "game_type": "multiple_choice_spelling"
}
```

#### Generate Multiple Games
```http
POST /api/generate-all-games
```
**Request Body:**
```json
{
  "words": [
    {"word": "example", "game_type": "multiple_choice_spelling"},
    {"word": "learning", "game_type": "suffix_completion"}
  ]
}
```

## 🎲 Game Types Explained

### 1. Multiple Choice Spelling Challenge
Students choose the correct spelling from 4 options.

### 2. Suffix Completion
Students complete a word by selecting the correct suffix from multiple options.

### 3. Fill in the Blanks
Students identify the complete word when some letters are replaced with blanks.

### 4. Error Detection
Students identify misspellings in presented words.

### 5. Guided Word Completion
Students complete partially shown words using contextual hints.

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
- Check if Python dependencies are installed: `pip list`
- Verify Python version: `python --version`
- Check for port conflicts (port 5000)

#### Groq API Errors
- Verify your API key in the `.env` file
- Test the connection: `http://localhost:5000/api/test-groq`
- Check Groq API usage limits and billing

#### Frontend Connection Issues
- Ensure backend is running on port 5000
- Check browser console for CORS errors
- Verify `API_BASE_URL` in the React component

#### Games Not Generating
- Check backend logs for detailed error messages
- Verify words are properly formatted (no special characters)
- Test with simpler, common words first

### Error Messages

- **"Unable to connect to the server"** - Backend is not running
- **"Failed to generate games"** - Check Groq API key and backend logs
- **"No games were generated"** - API returned empty results, check word formatting

## 🔒 Environment Variables

Create a `.env` file in the backend directory:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=1
```

## 📁 Project Structure

```
word-learning-games/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── .env                # Environment variables
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── index.js       # React entry point
│   ├── public/
│   └── package.json       # Node dependencies
└── README.md
```

## 🚀 Deployment

### Backend Deployment
1. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn app:app
   ```

2. Set environment variables on your hosting platform
3. Update CORS settings for production domains

### Frontend Deployment
1. Build the React app:
   ```bash
   npm run build
   ```

2. Deploy the `build` folder to your static hosting service
3. Update `API_BASE_URL` to point to your deployed backend

### Recommended Hosting Platforms
- **Backend:** Heroku, Railway, DigitalOcean, AWS
- **Frontend:** Vercel, Netlify, GitHub Pages

## 📊 Usage Tips

1. **Word Selection:** Use common, properly spelled words for best results
2. **Batch Processing:** Generate multiple games at once for efficiency  
3. **Game Variety:** Mix different game types for engaging learning experiences
4. **Error Handling:** The app provides fallback games if AI generation fails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review backend logs for detailed error messages
3. Test API connectivity using the health check endpoints
4. Open an issue on GitHub with detailed error information

## 🔮 Future Enhancements

- [ ] User authentication and saved games
- [ ] Printable worksheet generation
- [ ] Audio pronunciation guides
- [ ] Progress tracking and analytics
- [ ] Custom game difficulty levels
- [ ] Bulk word import from CSV files
- [ ] Multiple language support

---

Made with ❤️ for educators and learners everywhere!
