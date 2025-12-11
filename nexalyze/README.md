# 🚀 Nexalyze - AI-Powered Startup Intelligence Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

Nexalyze is a comprehensive AI-powered competitive intelligence platform for startup research. It combines multiple data sources with advanced AI analysis to provide deep insights into companies, markets, and competitive landscapes.

## ✨ Features

### 🔍 Company Search & Discovery
- Search 3,500+ startups from Y Combinator, Product Hunt, and more
- Filter by industry, stage, funding, and location
- Real-time data updates from multiple sources

### 🤖 AI-Powered Analysis
- **SWOT Analysis**: AI-generated strengths, weaknesses, opportunities, and threats
- **Competitive Intelligence**: Discover and analyze competitors
- **Market Research**: Industry trends, market size, and growth projections
- Powered by Google Gemini AI

### 💬 Conversational AI Assistant
- Natural language queries about companies and markets
- Context-aware responses with tool integration
- LangGraph-powered multi-step reasoning

### 📊 Report Generation
- Professional PDF and DOCX reports
- Multiple report types: Comprehensive, Competitive Analysis, Market Research
- AI-generated charts and visualizations

### 🔗 Multi-Source Data Integration
- **Y Combinator API**: Complete YC company database
- **Hacker News**: Trending discussions and mentions
- **Product Hunt**: Product launches and trends
- **GitHub**: Repository and developer data
- **News APIs**: Latest company news and announcements

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                          │
│   (Vite + TypeScript + Tailwind CSS + React Router)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│   (REST API + WebSocket + Rate Limiting + CORS)             │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │  AI Core  │  │  CrewAI   │  │ LangGraph │  │  Report   │ │
│  │  (Gemini) │  │  Agents   │  │   Agent   │  │  Service  │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐  ┌───────────────────────────┐│
│  │     Data Sources          │  │      Web Scraping        ││
│  │  (YC, HN, GitHub, etc.)   │  │   (ProductHunt, etc.)    ││
│  └───────────────────────────┘  └───────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│     PostgreSQL        │       │        Redis          │
│   (Company Data)      │       │   (Cache + Sessions)  │
└───────────────────────┘       └───────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI**: Google Gemini, CrewAI, LangGraph
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **PDF Generation**: WeasyPrint, ReportLab
- **Web Scraping**: BeautifulSoup, Selenium, aiohttp

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Routing**: React Router v6
- **Charts**: Recharts
- **Icons**: Lucide React

### Infrastructure
- **Container**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (in production)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Google Gemini API key

### Using Docker (Recommended)

1. **Clone and configure**
   ```bash
   git clone https://github.com/your-org/nexalyze.git
   cd nexalyze
   
   # Copy environment file
   cp .env.example .env
   
   # Edit .env and add your GEMINI_API_KEY
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend-react

# Install dependencies
npm install

# Start dev server
npm run dev
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `POSTGRES_URL` | PostgreSQL connection URL | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `SERP_API_KEY` | SerpAPI key for web search | No |
| `NEWS_API_KEY` | NewsAPI key | No |
| `GITHUB_TOKEN` | GitHub API token | No |
| `ENVIRONMENT` | development/staging/production | No |

### CORS Configuration
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Rate Limiting
```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

## 📚 API Documentation

### Core Endpoints

#### Search Companies
```http
GET /api/v1/companies?query={query}&limit={limit}
```

#### Chat with AI
```http
POST /api/v1/chat
{
  "query": "What are the top AI startups?",
  "user_session": "optional-session-id"
}
```

#### Generate Report
```http
POST /api/v1/generate-comprehensive-report
{
  "topic": "Fintech Market Analysis",
  "report_type": "comprehensive",
  "format": "pdf"
}
```

#### System Health
```http
GET /health
```

### Full API Reference
Visit `/docs` when running the backend for interactive Swagger documentation.

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Rebuild after changes
docker-compose build --no-cache

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📁 Project Structure

```
nexalyze/
├── backend/                    # FastAPI backend
│   ├── agents/                 # AI agents (CrewAI, LangGraph)
│   ├── api/                    # API routes and exceptions
│   ├── config/                 # Configuration settings
│   ├── database/               # Database connections
│   ├── services/               # Business logic services
│   ├── main.py                 # Application entry point
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container
├── frontend-react/             # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   ├── store/              # Zustand state
│   │   ├── types/              # TypeScript types
│   │   └── App.tsx             # Main application
│   ├── package.json            # Node dependencies
│   ├── Dockerfile              # Frontend container
│   └── nginx.conf              # Nginx configuration
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres
```

### Backend Not Starting
```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
docker-compose config
```

### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Y Combinator](https://www.ycombinator.com/) for the company database
- [Google Gemini](https://ai.google.dev/) for AI capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python framework
- [React](https://reactjs.org/) for the frontend framework
