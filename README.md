# WoodCarvings AI - Image Generation System

AI-powered image generation system for creating character design sheets using Google's Imagen models. Specifically designed for wood carving pattern generation with artist Chris Hammack's style.

## 🎨 Features

- **Multi-View Generation**: Creates 4-view character sheets (front, left, back, right)
- **Dual Rendering Modes**:
  - Sketch mode for pattern outlines
  - Color mode for reference visualization
- **Difficulty Levels**: Beginner, Intermediate, and Professional complexity
- **Multiple AI Engines**: Support for Imagen 3 and Imagen 4
- **Artist Style Integration**: Built-in style guide for consistent outputs

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python)
- **AI Provider**: Google Vertex AI & Generative AI
- **Image Generation**: Imagen 3/4 models
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **HTTP Client**: Axios

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud account with Vertex AI enabled
- Git

### Local Development

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd WoodCarvings
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   # Edit .env if needed
   ```

4. **Run Development Servers**

   Terminal 1 (Backend):
   ```bash
   python main.py
   # Backend runs on http://localhost:8000
   ```

   Terminal 2 (Frontend):
   ```bash
   cd frontend
   npm run dev
   # Frontend runs on http://localhost:3001
   ```

5. **Access Application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📦 Project Structure

```
WoodCarvings/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── render.yaml            # Render deployment config
├── .env.example           # Environment variables template
│
├── api/                   # API routes (future expansion)
├── models/                # Data models
│   └── schemas.py         # Pydantic schemas
├── services/              # Business logic
│   ├── prompt_service.py  # Prompt engineering
│   ├── vertex_service.py  # Vertex AI integration
│   ├── dropbox_service.py # Dropbox integration
│   └── artist_style_guide.txt
│
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main application
│   │   ├── main.jsx       # Entry point
│   │   └── config.js      # API configuration
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── scripts/               # Utility scripts (dev only)
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
GEMINI_API_KEY=            # Google Gemini API key
VERTEX_PROJECT_ID=         # Google Cloud project ID
VERTEX_LOCATION=           # Vertex AI region (e.g., us-central1)
VERTEX_API_KEY=            # GCP service account key (JSON)
DROPBOX_SHARED_FOLDER_LINK= # Optional: Dropbox reference folder
ALLOWED_ORIGINS=           # Frontend URLs (comma-separated)
```

#### Frontend (frontend/.env)
```env
VITE_API_URL=              # Backend API URL (empty for dev proxy)
```

## 🌐 API Endpoints

### System
- `GET /health` - Health check
- `GET /difficulty-levels` - List difficulty levels

### Cache
- `GET /cache/status` - Get cache status
- `POST /cache/refresh` - Refresh reference cache
- `DELETE /cache` - Clear cache

### Generation
- `POST /generate` - Generate character sheet
  ```json
  {
    "prompt": "A bear holding a fish",
    "mode": "sketch",
    "difficulty": "intermediate",
    "model_provider": "imagen_4"
  }
  ```

## 🎯 Usage

1. **Enter Concept**: Describe the character/subject
2. **Select AI Engine**: Choose Imagen 3 or 4
3. **Choose Mode**: Sketch or Color
4. **Set Complexity**: Beginner, Intermediate, or Professional
5. **Execute Generation**: Click to generate 4-view character sheet
6. **Export**: Download the generated sheet

## 🚢 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment guide.

### Quick Deploy to Render

1. Push code to GitHub
2. Create new Blueprint on Render
3. Connect repository (render.yaml auto-detected)
4. Configure environment variables
5. Deploy!

### Docker Deployment

```bash
# Build
docker build -t woodcarvings-api .

# Run
docker run -p 8000:8000 --env-file .env woodcarvings-api
```

## 🧪 Development

### Backend Testing
```bash
# Run backend
python main.py

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/difficulty-levels
```

### Frontend Testing
```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```

## 📚 Tech Stack

### Backend
- FastAPI - Web framework
- Uvicorn - ASGI server
- Pydantic - Data validation
- google-cloud-aiplatform - Vertex AI
- google-generativeai - Gemini API
- Pillow - Image processing

### Frontend
- React 18 - UI framework
- Vite - Build tool
- Tailwind CSS - Styling
- Framer Motion - Animations
- Axios - HTTP client
- Lucide React - Icons

## 🔒 Security

- Environment variables for sensitive data
- CORS configuration for allowed origins
- Input validation with Pydantic
- Service account authentication for GCP
- HTTPS enforced in production

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

[Add your license here]

## 🆘 Support

For issues and questions:
1. Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment help
2. Review API documentation at `/docs` endpoint
3. Check logs for error messages
4. Verify environment variables

## 🙏 Acknowledgments

- Artist style by Chris Hammack
- Powered by Google Vertex AI and Imagen models
- Built with FastAPI and React
