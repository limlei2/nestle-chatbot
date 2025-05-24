# Nestlé Chatbot (MadeWithNestle.ca AI Assistant)

A full-stack AI-powered chatbot for MadeWithNestle.ca that scrapes MadeWithNestle.ca and answers recipe and product-related questions using both a vector database and a Neo4j graph database. 
Built with React, FastAPI, Playwright, Azure AI Search, Azure OpenAI, and Neo4j.

## Getting Started

### Prerequisites

- Node.js
- Python 3.11
- Neo4j
- Azure OpenAI + Azure AI Search


### Configuration

#### Frontend
Create a `.env` file in the `frontend/` directory as such.

#### `frontend/.env`
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

#### Backend
Create a `.env` file in the `backend/` directory as such, and fill in appropriate credentials.

#### `backend/.env`
```env
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_VERSION=
AZURE_AI_SEARCH_ENDPOINT=
AZURE_AI_SEARCH_KEY=
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
```

### Installation (Backend)

1. Navigate to backend directory
2. Create a virtual environment on Python 3.11 `python3.11 -m venv venv`
3. Activate the virtual environment `source venv/bin/activate`
4. Run the scraper to scrape site data and populate vector and graph databases `python scraper.py`
5. Run `uvicorn main:app --reload` to run the API server on http://localhost:8000

### Installation (Frontend)
1. Navigate to frontend directory
2. Run `npm install` to install all required dependencies.
3. Run `npm start` to start development server on http://localhost:3000

## Technologies and Frameworks Used

- React.js — Frontend interface for the chatbot.
- FastAPI — Python web framework powering the backend API.
- Playwright (async) — Used to scrape the entire madewithnestle.ca website.
- BeautifulSoup — HTML parsing and content cleaning for scraper preprocessing.
- Neo4j — Graph database used to store structured recipe information with relationships between recipes, ingredients, skill level, and tags.
- Azure OpenAI — Powers the chatbot’s conversational responses using retrieval-augmented generation (RAG), and used to embed text for the vector database.
- Azure AI Search — Vector search engine for semantic retrieval of recipe and site content using embeddings.

## Limitations
