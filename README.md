# AI Security Scanner

Find security vulnerabilities in any codebase using AI — runs entirely on your own machine, completely free, no data ever leaves your computer.

---

## What it does

Point it at any project folder and it will:

1. Walk through every source code file in your project
2. Automatically redact any secrets, API keys, or passwords it finds before the AI sees anything
3. Send the cleaned code to a local AI model (Mistral, running on your machine)
4. Get back a list of real security issues — SQL injection, hardcoded credentials, insecure deserialization, command injection, and more
5. Generate a beautiful HTML report with severity levels, risk explanations, and specific fix suggestions

Everything runs locally. No cloud, no accounts, no cost.

---

## Example output

```
Step 1/4  Walking codebase...
          Found 24 files (3,847 lines)

Step 2/4  Stripping secrets...
          [!] config.py — 2 secret(s) found and redacted

Step 3/4  Running AI analysis...
  [1/24] app.py... 3 issue(s) found
  [2/24] auth.py... 1 issue(s) found
  [3/24] utils.py... clean
  ...

Step 4/4  Generating report...

Report saved: reports/scan_2026-04-18_14-32.html
```

Open the HTML report in any browser to see your findings.

---

## Supported languages

Python, JavaScript, TypeScript, React (JSX/TSX), PHP, Java, Go, Ruby, C#, C/C++, SQL, Shell scripts, YAML/JSON config files.

---

## Requirements

- A Mac, Windows, or Linux computer
- Python 3.8 or newer
- 8GB RAM (for running the local AI model)
- ~5GB free disk space (for the AI model download)
- Internet connection only for the first-time model download

---

## Quick setup (5 minutes)

### Step 1 — Download the project

```bash
git clone https://github.com/YOUR_USERNAME/ai-security-scanner.git
cd ai-security-scanner
```

### Step 2 — Set up Python environment

```bash
python -m venv venv
```

Activate it:

- Mac/Linux: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`

You should see `(venv)` appear at the start of your terminal line.

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install Ollama (the local AI engine)

Go to **https://ollama.com/download** and install it like any normal application.

Then download the Mistral AI model (one-time, ~4GB):

```bash
ollama pull mistral
```

This takes 5–10 minutes. You only need to do this once.

### Step 5 — Run your first scan

```bash
python main.py ./path/to/your/project
```

Then open the report:

```bash
# Mac
open reports/scan_*.html

# Windows
start reports/scan_*.html

# Linux
xdg-open reports/scan_*.html
```

---

## Usage

```bash
# Scan a project
python main.py ./my-project

# Scan with a custom report name
python main.py ./my-project --output my-report.html

# Scan the current folder
python main.py .
```

---

## Switching to a different AI (optional)

By default the scanner uses Mistral running locally via Ollama — completely free and offline.

If you want to use a cloud AI instead, open `config.py` and change one line:

```python
PROVIDER = "ollama"   # change this to: "claude", "openai", or "groq"
```

Then set your API key:

```bash
# Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Groq (has a free tier)
export GROQ_API_KEY="gsk_..."
```

Install the matching library:

```bash
pip install anthropic   # for Claude
pip install openai      # for OpenAI
pip install groq        # for Groq
```

That's it. No other file needs to change. See [docs/providers.md](docs/providers.md) for a full comparison of all providers.

---

## Project structure

```
ai-security-scanner/
├── scanner/
│   ├── walker.py      # finds all code files in your project
│   ├── stripper.py    # redacts secrets before AI sees anything
│   ├── analyzer.py    # sends code to AI, parses security findings
│   └── reporter.py    # generates the HTML report
├── tests/             # test files for each module
├── docs/              # detailed documentation
├── reports/           # your scan reports land here (git-ignored)
├── config.py          # change AI provider here
├── requirements.txt   # Python dependencies
└── main.py            # run this to start a scan
```

---

## Privacy guarantee

Your code never goes anywhere unexpected:

- Steps 1–3 (walk, strip, chunk) run entirely on your machine
- Secrets are redacted **before** anything reaches the AI
- When using Ollama (default), the AI itself runs on your machine — nothing leaves your computer at all
- When using a cloud API (Claude/OpenAI/Groq), only cleaned code with secrets already removed is sent

---

## License

MIT — free to use, modify, and distribute.