# Security Analyst Copilot

AI-powered cybersecurity risk analysis using RAG (Retrieval-Augmented Generation).

## Architecture

```
Next.js Frontend → FastAPI Backend → MongoDB
                              ↓
                     Retrieval Layer
                     Context Builder
                     Anthropic API (Claude)
                     Response Formatter
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY and MongoDB URI
```

Start MongoDB (if local):
```bash
brew services start mongodb-community  # macOS
# or: docker run -d -p 27017:27017 mongo
```

Run FastAPI:
```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
npm run dev
```

App: http://localhost:3000

### 3. Load demo data

Click **"Load demo data"** in the UI, or:

```bash
curl -X POST http://localhost:8000/assessments/seed
```

This seeds 7 realistic risks for a fintech company (AcmePay).

## Project Structure

```
backend/
  app/
    api/          # FastAPI routes
    core/         # Config/settings
    db/           # MongoDB connection
    models/       # Pydantic schemas
    services/
      retrieval.py      # Pulls risks from MongoDB
      context_builder.py # Structures data for LLM
      llm.py            # Anthropic API calls
  requirements.txt

frontend/
  src/
    app/          # Next.js pages
    components/   # ChatMessage, SuggestedPrompts, SeverityBadge
    lib/          # API client
    types/        # TypeScript types
```

## Key Concepts

**Why this isn't a generic chatbot:**
- Retrieval layer pulls real risk data from MongoDB before every query
- Context builder structures that data into LLM-optimised format
- LLM only reasons over your actual data — no hallucination of fake risks
- Conversation memory enables follow-up questions

**Extending this:**
- Add more risk categories (Network, Compliance, Cloud)
- Connect to real scanners (AWS Security Hub, Nessus API)
- Add a risk dashboard view alongside the copilot
- Implement "Consultant Mode" with tone/audience switching
- Persist chat history per assessment in MongoDB

## Deployment

### Backend (Railway)
- URL: https://security-copilot-production.up.railway.app/
- Health check: https://security-copilot-production.up.railway.app/health
- API docs: https://security-copilot-production.up.railway.app/docs

### Frontend (Vercel)
- URL: https://security-copilot-six.vercel.app/ 

### Environment Variables
Set all variables from `.env.example` in Railway dashboard under Variables tab.