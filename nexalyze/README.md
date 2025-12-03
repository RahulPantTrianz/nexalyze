# 🚀 Nexalyze - AI-Powered Competitive Intelligence Platform

<div align="center">

![Nexalyze](https://img.shields.io/badge/Nexalyze-v2.0-purple?style=for-the-badge)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Claude 4.5](https://img.shields.io/badge/Claude-Sonnet%204.5-8B5CF6?style=for-the-badge)](https://www.anthropic.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

**Transform Startup Research with AI-Powered Intelligence**

[Quick Start](#-quick-start) • [Features](#-key-features) • [Demo](#-demo) • [API Docs](#-api-documentation)

</div>

---

## 📖 Overview

**Nexalyze** is a cutting-edge competitive intelligence platform that leverages AI and multi-source data aggregation to provide deep insights about startups, market landscapes, and competitive dynamics. Built for investors, researchers, and entrepreneurs who need actionable intelligence.

### 🎯 The Problem

- Manual startup research is time-consuming and fragmented
- Data scattered across multiple sources (YC, Product Hunt, Crunchbase, etc.)
- Lack of AI-powered insights and competitive analysis
- No unified platform for comprehensive market intelligence

### 💡 Our Solution

An all-in-one AI-powered platform that:

- 🔍 **Aggregates** data from 6+ sources automatically
- 🤖 **Enriches** data using Claude Sonnet 4.5 via AWS Bedrock
- 📊 **Analyzes** competitive landscapes with advanced AI
- 🕸️ **Visualizes** relationships through interactive knowledge graphs
- 📄 **Generates** professional AI-powered PDF reports with charts

---

## ✨ Key Features

### 🤖 AI-Powered Intelligence
- **Claude Sonnet 4.5** integration via AWS Bedrock (latest and most powerful LLM)
- **Natural Language Chat** - Ask questions about any company or market
- **Intelligent Analysis** - AI-generated competitive intelligence and SWOT analysis
- **Auto-Generated Reports** - LLM-written executive summaries and insights

### 🌐 Multi-Source Data Aggregation
- **Y Combinator** - 3,500+ companies via official API
- **Product Hunt** - Featured products and startups
- **BetaList** - Early-stage startup directory
- **Startup Ranking** - Global startup database
- **SERP API** - Real-time Google search integration
- **Hacker News** - Community mentions and discussions

### 📊 Advanced Analytics
- **Company Profiles** - Comprehensive company information
- **Competitive Analysis** - AI-powered competitor identification
- **Market Research** - Industry trends and market sizing
- **Knowledge Graphs** - Interactive Neo4j-powered relationship visualization
- **Trend Detection** - Emerging patterns and opportunities

### 📄 Professional Reporting
- **AI-Generated HTML to PDF** - Beautiful reports using WeasyPrint
- **Custom Charts** - Dynamic visualizations with Plotly and Matplotlib
- **LLM-Written Content** - Executive summaries, market analysis, recommendations
- **Multiple Formats** - Export as PDF or DOCX

### 🎨 Modern UI
- **Glassmorphism Design** - Premium aesthetic with backdrop blur effects
- **Responsive Layout** - Mobile-optimized with touch-friendly interactions
- **Smooth Animations** - Professional transitions and effects
- **Interactive Visualizations** - Dynamic charts and knowledge graphs

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   Frontend (Streamlit)                      │
│         Chat • Search • Analysis • Reports • Graphs         │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                      │
│  ┌──────────┬────────────┬──────────────┬───────────────┐  │
│  │   Chat   │   Data     │   Research   │    Report     │  │
│  │  Agent   │  Service   │   Service    │   Service     │  │
│  │  (LLM)   │ (Scraping) │  (Analysis)  │ (Generation)  │  │
│  └──────────┴────────────┴──────────────┴───────────────┘  │
└──────────────────────────┬─────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬──────────────┐
        ▼                  ▼                  ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
│    Neo4j     │  │  PostgreSQL  │  │    Redis    │  │ AWS Bedrock  │
│  Knowledge   │  │  Structured  │  │   Caching   │  │  Claude 4.5  │
│    Graph     │  │     Data     │  │             │  │     LLM      │
└──────────────┘  └──────────────┘  └─────────────┘  └──────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **AI/ML**: AWS Bedrock (Claude Sonnet 4.5), CrewAI
- **Databases**: 
  - Neo4j 5.13 (Knowledge Graph)
  - PostgreSQL 15 (Structured Data)
  - Redis 7 (Caching)
- **Data Collection**: BeautifulSoup, aiohttp, SERP API
- **Report Generation**: WeasyPrint (HTML to PDF), python-docx, ReportLab

### Frontend
- **Framework**: Streamlit
- **Visualization**: Plotly, Matplotlib, NetworkX
- **UI**: Custom CSS with Glassmorphism effects

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Cloud**: AWS (Bedrock for LLM)
- **Authentication**: AWS IAM (Profile-based)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS credentials with Bedrock access
- Minimum 8GB RAM, 20GB disk space

### Installation

1. **Navigate to project directory**
   ```bash
   cd c:\Hackathon\nexalyze
   ```

2. **Configure AWS Credentials**
   
   Ensure you have AWS profile named `amplify` in `~/.aws/credentials`:
   ```ini
   [amplify]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   region = us-west-2
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to initialize** (~30 seconds)
   ```bash
   docker-compose logs -f
   ```

5. **Access the application**
   
   | Service | URL | Description |
   |---------|-----|-------------|
   | 🎨 **Frontend** | http://localhost:8501 | Main UI |
   | 🔌 **API** | http://localhost:8000 | Backend API |
   | 📚 **API Docs** | http://localhost:8000/docs | Swagger UI |
   | 🕸️ **Neo4j** | http://localhost:7474 | Graph Browser |

   **Neo4j Credentials**: `neo4j` / `password123`

6. **Verify installation**
   ```bash
   curl http://localhost:8000/health
   ```
   
   Expected: `{"status": "healthy"}`

---

## 🎬 Demo

### 1. 💬 Chat with AI
Ask natural language questions about startups:
- "What is a fintech startup?"
- "Tell me about successful AI companies"
- "Compare OpenAI and Anthropic"

### 2. 🔍 Search Companies
Search across 3,500+ startups:
- Filter by industry (AI, FinTech, Healthcare, etc.)
- View detailed company profiles
- See funding history and metrics

### 3. 📊 Generate Analysis
Deep dive into any company:
- Market position and size
- Top competitors (AI-identified)
- SWOT analysis
- Recent news and trends

### 4. 📄 Create Reports
Generate professional PDF reports:
- AI-written executive summaries
- Custom charts and visualizations
- Comprehensive market analysis
- Competitive landscape overview

### 5. 🕸️ Explore Knowledge Graphs
Visualize company relationships:
- Interactive Neo4j-powered graphs
- Competitor networks
- Market segment connections
- Investor relationships

---

## 📚 Features in Detail

### 🗣️ AI Chat Interface

**Powered by**: Claude Sonnet 4.5 via AWS Bedrock

**Capabilities**:
- Natural language conversations
- Context-aware responses
- Session memory
- Multi-turn dialogues

**Example Queries**:
```
"What are the key trends in AI startups?"
"How does Stripe's business model work?"
"Which YC companies raised Series A in 2024?"
```

**API Endpoint**:
```bash
POST /api/v1/chat
{
  "query": "What makes a successful startup?",
  "user_session": "optional_session_id"
}
```

### 🔍 Intelligent Company Search

**Features**:
- Multi-source aggregation (6+ sources)
- Redis-cached results (5min TTL)
- Fuzzy matching
- Real-time data updates

**Search Filters**:
- Industry (AI, FinTech, Healthcare, EdTech, SaaS, E-commerce)
- Stage (Seed, Series A-E, IPO)
- Location (Global coverage)
- Funding Range

**API Endpoint**:
```bash
GET /api/v1/companies?query=AI&limit=10
```

### 📊 Competitive Intelligence

**Analysis Includes**:
- 📈 Market size and growth rate
- 🏆 Top 5 AI-identified competitors
- 📰 Latest news (via SERP API)
- 💪 SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
- 🎯 Competitive advantages
- 💰 Funding history

**API Endpoint**:
```bash
POST /api/v1/analyze
{
  "company_name": "Stripe",
  "include_competitors": true
}
```

### 📄 AI-Powered Report Generation

**Report Types**:
1. **Comprehensive** - Full company + market analysis
2. **Competitive Analysis** - Focus on competition
3. **Market Research** - Industry trends and opportunities

**AI-Generated Content**:
- Executive Summary (LLM-written)
- Market Analysis
- Technology Insights
- Financial Overview
- Strategic Recommendations

**Output Formats**:
- PDF (via WeasyPrint HTML to PDF)
- HTML (beautiful, responsive)
- DOCX (optional)

**API Endpoint**:
```bash
POST /api/v1/generate-comprehensive-report
{
  "topic": "AI Startups 2024",
  "report_type": "comprehensive",
  "format": "pdf"
}
```

### 🕸️ Knowledge Graph Visualization

**Features**:
- Interactive Neo4j-powered graphs
- Company-to-company relationships
- Competitor networks
- Investor connections
- Market segment mappings

**API Endpoint**:
```bash
GET /api/v1/knowledge-graph/by-name/{company_name}
```

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | AI chat interface |
| `GET` | `/companies` | Search companies |
| `POST` | `/analyze` | Analyze company |
| `POST` | `/scrape/yc` | Scrape Y Combinator |
| `POST` | `/scrape/comprehensive` | Multi-source scraping |
| `GET` | `/knowledge-graph/by-name/{name}` | Get knowledge graph |
| `POST` | `/generate-comprehensive-report` | Generate AI report |
| `GET` | `/hacker-news/latest-stories` | Latest HN stories |

### Interactive Documentation
Full Swagger UI available at: **http://localhost:8000/docs**

---

## 🤖 LLM Integration Details

### AWS Bedrock Configuration

| Parameter | Value |
|-----------|-------|
| **Model** | Claude Sonnet 4.5 |
| **Model ID** | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| **Provider** | AWS Bedrock |
| **Region** | us-west-2 |
| **Profile** | amplify |
| **Temperature** | 0.3 |

### LLM Usage Points

1. **Chat Interface** - Natural language Q&A
2. **Company Analysis** - Competitive intelligence generation
3. **Data Enrichment** - Clean and classify scraped data
4. **Report Generation** - Write executive summaries and insights
5. **Research Service** - Synthesize information from multiple sources

---

## 📊 Data Sources

| Source | Type | Coverage | Reliability | Status |
|--------|------|----------|-------------|--------|
| **Y Combinator** | API | 3,500+ | ⭐⭐⭐⭐⭐ | ✅ Active |
| **Product Hunt** | Scraping | Unlimited | ⭐⭐⭐⭐ | ✅ Active |
| **BetaList** | Scraping | 1,000+ | ⭐⭐⭐ | ✅ Active |
| **Startup Ranking** | Scraping | 10,000+ | ⭐⭐⭐ | ✅ Active |
| **SERP API** | Search | Unlimited | ⭐⭐⭐⭐⭐ | ✅ Active |
| **Hacker News** | API | Real-time | ⭐⭐⭐⭐⭐ | ✅ Active |

---

## 💾 Database Schema

### Neo4j (Knowledge Graph)

**Nodes**:
```cypher
(:Company {
  name: string,
  description: string,
  industry: string,
  founded_year: int,
  location: string,
  website: string,
  stage: string
})
```

**Relationships**:
```cypher
(Company)-[:COMPETES_WITH]->(Company)
(Company)-[:OPERATES_IN]->(Market)
(Investor)-[:INVESTED_IN]->(Company)
```

### PostgreSQL (Structured Data)
- Company records
- User sessions
- Scraping history
- Analytics data

### Redis (Caching)
- Search results (TTL: 5min)
- API rate limiting
- Session storage

---

## ⚙️ Configuration

### Environment Variables

Edit `docker-compose.yml`:

```yaml
environment:
  # AWS Bedrock
  - AWS_PROFILE=amplify
  - AWS_REGION=us-west-2
  - BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
  
  # Optional APIs
  - SERP_API_KEY=${SERP_API_KEY}
  
  # Databases
  - NEO4J_URI=bolt://neo4j:7687
  - NEO4J_USER=neo4j
  - NEO4J_PASSWORD=password123
  - POSTGRES_URL=postgresql://postgres:password123@postgres:5432/nexalyze
  - REDIS_URL=redis://redis:6379
```

### Optional: SERP API Key

For enhanced Google search integration:

1. Get free key at [serpapi.com](https://serpapi.com)
2. Set environment variable:
   ```bash
   export SERP_API_KEY=your_key_here
   ```

---

## 🐛 Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose down
docker-compose up -d --build
```

### LLM Not Responding

```bash
# Verify AWS credentials
cat ~/.aws/credentials

# Test Bedrock access
aws bedrock list-foundation-models --region us-west-2 --profile amplify

# Restart backend
docker-compose restart backend
```

### Database Connection Failed

```bash
# Check all services
docker-compose ps

# Restart everything
docker-compose down && docker-compose up -d

# Wait 30 seconds for initialization
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Restart
docker-compose restart frontend

# Access at http://localhost:8501
```

---

## 📈 Project Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~6,000+ |
| **API Endpoints** | 40+ |
| **Data Sources** | 6+ |
| **Databases** | 3 (Neo4j, PostgreSQL, Redis) |
| **Docker Services** | 5 |
| **Companies Available** | 3,500+ |
| **Average Response Time** | < 3 seconds |
| **LLM Integration Points** | 5 major features |

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Real-time funding tracking
- [ ] Email alerts for updates
- [ ] Mobile app (React Native)
- [ ] Advanced filtering
- [ ] Sentiment analysis
- [ ] Predictive modeling
- [ ] API authentication
- [ ] Multi-user support

### Technical Improvements
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Performance monitoring
- [ ] GraphQL API
- [ ] WebSocket real-time updates

---

## 🙏 Acknowledgments

- **AWS Bedrock** for Claude Sonnet 4.5 access
- **Y Combinator** for comprehensive startup API
- **Anthropic** for Claude AI
- **Neo4j** for graph database
- **Streamlit** for rapid UI development

---

## 📞 Support

For questions or issues:

1. Check [Troubleshooting](#-troubleshooting) section
2. View API docs at http://localhost:8000/docs
3. Check logs: `docker-compose logs -f`
4. Review documentation in `/docs` folder

---

## 🚀 Quick Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs (real-time)
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Restart a service
docker-compose restart backend

# Check service status
docker-compose ps

# Rebuild and start
docker-compose up -d --build

# Health check
curl http://localhost:8000/health
```

---

<div align="center">

## 🎉 Built for Hackathon

**Nexalyze** - AI-Powered Competitive Intelligence

Transforming startup research with cutting-edge AI 🚀

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/)

---

### Created by Algorithm Avengers

</div>
