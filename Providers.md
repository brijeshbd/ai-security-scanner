# AI Provider Guide

The scanner works with four different AI providers. You switch between them by editing one line in `config.py`. Everything else stays the same.

---

## Comparison

| Provider | Cost | Internet needed | Speed | Quality | Best for |
|---|---|---|---|---|---|
| Ollama (default) | Free forever | No (after model download) | Medium | Good | Privacy, offline use, no budget |
| Groq | Free tier available | Yes | Very fast | Good | Speed, free cloud option |
| Claude | Pay per use | Yes | Fast | Excellent | Deep analysis, large codebases |
| OpenAI | Pay per use | Yes | Fast | Excellent | Deep analysis, large codebases |

---

## Provider 1 — Ollama (default, free)

Runs an open-source AI model directly on your laptop. No internet after initial setup, no cost, no account needed.

**Setup:**

1. Install Ollama from https://ollama.com/download
2. Pull a model:
   ```bash
   ollama pull mistral        # recommended — good balance of speed and quality
   ollama pull llama3         # alternative — slightly better quality, larger
   ollama pull codellama      # alternative — specifically trained on code
   ```
3. In `config.py`:
   ```python
   PROVIDER     = "ollama"
   OLLAMA_MODEL = "mistral"   # change to llama3 or codellama if you prefer
   ```

**No API key needed.**

---

## Provider 2 — Groq (free tier, fast)

Groq offers a generous free tier with very fast inference. Good option if you want cloud AI without paying.

**Setup:**

1. Sign up at https://console.groq.com (free)
2. Create an API key in your dashboard
3. Install the library:
   ```bash
   pip install groq
   ```
4. Set your key:
   ```bash
   export GROQ_API_KEY="gsk_your_key_here"
   ```
5. In `config.py`:
   ```python
   PROVIDER   = "groq"
   GROQ_MODEL = "llama3-8b-8192"   # or "mixtral-8x7b-32768" for better quality
   ```

---

## Provider 3 — Anthropic Claude

Claude is excellent at understanding code context and gives detailed, accurate findings. Costs money but has very low per-scan cost (usually a few cents for a medium project).

**Setup:**

1. Sign up at https://console.anthropic.com
2. Create an API key
3. Install the library:
   ```bash
   pip install anthropic
   ```
4. Set your key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your_key_here"
   ```
5. In `config.py`:
   ```python
   PROVIDER      = "claude"
   CLAUDE_MODEL  = "claude-3-haiku-20240307"   # cheapest, fast
   # or
   CLAUDE_MODEL  = "claude-sonnet-4-5"         # better quality, costs more
   ```

---

## Provider 4 — OpenAI

GPT-4o and GPT-4o-mini are strong at code analysis. Similar cost to Claude.

**Setup:**

1. Sign up at https://platform.openai.com
2. Create an API key
3. Install the library:
   ```bash
   pip install openai
   ```
4. Set your key:
   ```bash
   export OPENAI_API_KEY="sk-your_key_here"
   ```
5. In `config.py`:
   ```python
   PROVIDER     = "openai"
   OPENAI_MODEL = "gpt-4o-mini"   # cheaper
   # or
   OPENAI_MODEL = "gpt-4o"        # better quality
   ```

---

## Setting API keys permanently (so you don't have to re-export every session)

**Mac/Linux** — add to your `~/.zshrc` or `~/.bashrc`:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."
```
Then run `source ~/.zshrc` to apply.

**Windows** — in PowerShell:
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-...","User")
```

---

## Adding a new provider

The codebase is designed so adding a new provider takes about 10 lines of code.

Open `scanner/analyzer.py` and:

1. Add a new function following the same pattern as `_call_ollama`, `_call_claude` etc.
2. Add a config entry for the model name in `config.py`
3. Register it in the `PROVIDERS` dict in `analyzer.py`

That's it — `main.py` and all other files stay untouched.