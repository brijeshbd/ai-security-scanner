"""
config.py — Central configuration for AI Security Scanner
==========================================================
This is the ONLY file you need to edit to switch between AI providers.

Supported providers:
  - "ollama"     Local model via Ollama (free, no API key needed)
  - "claude"     Anthropic Claude API  (needs ANTHROPIC_API_KEY)
  - "openai"     OpenAI GPT API        (needs OPENAI_API_KEY)
  - "groq"       Groq API              (needs GROQ_API_KEY, very fast & free tier)

Quick switch example — to use Claude instead of Ollama:
  1. Set PROVIDER = "claude"
  2. Set ANTHROPIC_API_KEY = "your-key-here"  OR export it in your shell:
       export ANTHROPIC_API_KEY="sk-ant-..."
  3. Run the scanner as normal: python main.py ./my-project
"""

import os

# ── Provider selection ────────────────────────────────────────────────────────
# Change this one line to switch your AI provider.
PROVIDER = "ollama"   # "ollama" | "claude" | "openai" | "groq"

# ── Ollama (local, free) ──────────────────────────────────────────────────────
OLLAMA_MODEL   = "mistral"          # any model you have pulled: mistral, llama3, codellama
OLLAMA_HOST    = "http://localhost:11434"  # default Ollama server address

# ── Anthropic Claude ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-3-haiku-20240307"   # fast + cheap; change to claude-3-5-sonnet for deeper analysis

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = "gpt-4o-mini"     # change to "gpt-4o" for deeper analysis

# ── Groq (free tier, very fast) ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama3-8b-8192"    # change to "mixtral-8x7b-32768" for better results

# ── Scanner behaviour ─────────────────────────────────────────────────────────
MAX_FILE_CHARS    = 8000    # truncate files larger than this before sending to AI
REPORTS_DIR       = "reports"       # folder where HTML reports are saved