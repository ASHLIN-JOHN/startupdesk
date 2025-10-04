# VC Pitch Deck Analyzer

## Overview

The VC Pitch Deck Analyzer is a FastAPI-based web application that automates the evaluation of startup pitch decks for venture capital analysis. The system parses presentation files (PDF and PPTX), extracts content, and uses AI-powered agents to score various aspects of the pitch deck including market opportunity, team quality, product differentiation, and traction metrics. Results are delivered as structured evaluation reports with scores and detailed notes.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI** serves as the core web framework, chosen for its modern async support, automatic API documentation, and high performance
- CORS middleware enables cross-origin requests for flexible frontend integration
- Static file serving delivers the web interface directly from the FastAPI application

### Document Processing Pipeline
- **Multi-format parsing** supports PPTX (python-pptx) and PDF (pymupdf) files
- Text extraction occurs at the slide/page level to maintain content structure
- Parser abstraction layer (`parsers.py`) routes to appropriate handler based on file extension
- Extracted content is formatted as structured text with slide/page annotations for downstream analysis
- Note: Legacy PPT format is not supported, only modern PPTX files

### AI Evaluation Architecture
- **Groq API integration** provides LLM-powered scoring and analysis using the Mixtral-8x7b model
- **Multi-agent evaluation system** (via CrewAI framework) orchestrates specialized analysis across different pitch deck dimensions:
  - Market Size and Opportunity analysis
  - Team Quality and Experience assessment
  - Product Differentiation and Innovation review
  - Traction and Growth Metrics evaluation
- Each agent generates both numerical scores (1-10 scale) and qualitative evaluation notes
- Structured JSON responses ensure consistent data format for aggregation and reporting

### Data Flow
1. User uploads pitch deck with metadata (company name, sector, stage, funding ask)
2. File stored in local uploads directory
3. Document parser extracts and structures content
4. Evaluation crew processes content through specialized agents
5. Groq API calls generate category-specific scores and notes
6. Results cached in-memory and stored as JSON reports
7. Frontend receives comprehensive evaluation response

### Storage Strategy
- **Local file system** used for uploaded decks (uploads/) and generated reports (reports/)
- In-memory caching (`evaluation_cache` dict) stores evaluation results for quick retrieval
- Report files saved as JSON with UUID-based naming for uniqueness

### Communication Layer
- Email notifications via **SendGrid API** for delivering evaluation reports
- HTML/JSON response formats support both web interface and API consumers
- Static HTML frontend provides user interface for uploads and result viewing

## External Dependencies

### AI/ML Services
- **Groq API** - Primary LLM service for content analysis and scoring (Mixtral-8x7b-32768 model)
- **CrewAI** - Agent orchestration framework for multi-agent evaluation workflow

### Document Processing
- **python-pptx** - PowerPoint (.pptx) file parsing and text extraction (legacy .ppt not supported)
- **pymupdf** - PDF document parsing and text extraction

### Communication Services
- **SendGrid** - Transactional email service for report delivery

### Core Libraries
- **FastAPI** - Web framework and API server
- **python-multipart** - File upload handling
- **python-dotenv** - Environment variable management

### Frontend
- Vanilla HTML/CSS/JavaScript served via FastAPI static files
- No external frontend framework dependencies