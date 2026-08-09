# JARVIS Engine Setup

## Quick Start
1. Install dependencies: uv sync
2. Copy .env.example to .env
3. Start server: uv run python start.py

## AI Providers

### Ollama (Local - Default)
- Install Ollama from https://ollama.ai
- Run: ollama pull llama3.2:3b
- Start: ollama serve
- No API key needed

### OpenRouter (Cloud Fallback)
- Sign up at https://openrouter.ai
- Get free API key
- Add to .env: OPENROUTER_API_KEY=your_key
- Free models: google/gemma-4-27b-it:free

## Provider Priority
1. Ollama (local, free, private)
2. OpenRouter (cloud, free tier available)

JARVIS automatically uses the first 
available provider.
