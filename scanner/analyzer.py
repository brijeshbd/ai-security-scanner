"""
scanner/analyzer.py — AI analysis engine
=========================================
Sends cleaned code to whichever AI provider is configured in config.py.
Adding a new provider = adding one function + one entry in _get_response().
"""

import json
import os
import config

# ── System prompt ─────────────────────────────────────────────────────────────
# Shared across all providers — the AI always gets the same instructions.

SYSTEM_PROMPT = """You are an expert security engineer performing a thorough code security audit.
Your job is to find real, exploitable security vulnerabilities in the code you are given.

You must check for these vulnerability categories:
- Injection flaws: SQL injection, command injection, XSS, LDAP injection
- Broken authentication: hardcoded credentials, weak password checks, insecure sessions
- Sensitive data exposure: logging secrets, sending credentials in plaintext
- Insecure direct object references: missing authorization checks
- Security misconfiguration: debug mode on, open CORS, insecure headers
- Vulnerable dependencies: use of known-insecure functions or patterns
- Insecure deserialization: pickle, eval, exec on user input
- Insufficient logging: missing audit trails for sensitive actions
- Business logic flaws: missing input validation, race conditions

For each vulnerability you find, respond ONLY with a valid JSON array.
Each item must have exactly these fields:
{
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "type": "short name e.g. SQL Injection",
  "line": line number as integer or null,
  "description": "one sentence — what the vulnerability is",
  "risk": "one sentence — what an attacker could do",
  "fix": "concrete, specific fix or code recommendation"
}

Rules:
- Return ONLY the JSON array. No intro, no explanation, no markdown fences.
- If you find no vulnerabilities return: []
- Do not invent vulnerabilities. Only report what is clearly visible.
- Order by severity: CRITICAL first, then HIGH, MEDIUM, LOW.
"""


def _build_user_prompt(filepath, content):
    filename  = os.path.basename(filepath)
    extension = os.path.splitext(filename)[1]
    return (f"Analyze this file for security vulnerabilities.\n\n"
            f"File: {filename}\nLanguage: {extension}\n\nCode:\n{content}\n\n"
            f"Return findings as a JSON array only.")


# ── Provider implementations ──────────────────────────────────────────────────

def _call_ollama(prompt):
    """Calls a locally running Ollama model. No API key required."""
    import ollama
    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": prompt},
        ],
        options={"temperature": 0, "num_predict": 2000},
    )
    return response["message"]["content"].strip()


def _call_claude(prompt):
    """Calls Anthropic Claude API. Requires ANTHROPIC_API_KEY in config."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("Run: pip install anthropic")

    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not set in config.py or environment.")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _call_openai(prompt):
    """Calls OpenAI API. Requires OPENAI_API_KEY in config."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Run: pip install openai")

    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in config.py or environment.")

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        temperature=0,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _call_groq(prompt):
    """Calls Groq API (free tier available). Requires GROQ_API_KEY in config."""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("Run: pip install groq")

    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in config.py or environment.")

    client = Groq(api_key=config.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


# ── Provider router ───────────────────────────────────────────────────────────

PROVIDERS = {
    "ollama": _call_ollama,
    "claude": _call_claude,
    "openai": _call_openai,
    "groq":   _call_groq,
}


def _get_response(prompt):
    """Routes to the correct provider based on config.PROVIDER."""
    provider = config.PROVIDER.lower()
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Choose from: {', '.join(PROVIDERS.keys())}"
        )
    return PROVIDERS[provider](prompt)


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_file(filepath, cleaned_content):
    """
    Analyzes one file. Returns a list of finding dicts.
    cleaned_content: file text already processed by stripper.py
    """
    if not cleaned_content or len(cleaned_content.strip()) < 10:
        return []

    # Truncate very large files to stay within model context limits
    content = cleaned_content
    if len(content) > config.MAX_FILE_CHARS:
        content = content[:config.MAX_FILE_CHARS] + "\n\n# [FILE TRUNCATED]"

    print(f"  Analyzing: {os.path.basename(filepath)}...", end=" ", flush=True)

    try:
        raw = _get_response(_build_user_prompt(filepath, content))

        # Strip markdown fences if model added them despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        if not raw or raw == "[]":
            print("clean")
            return []

        findings = json.loads(raw)

        if not isinstance(findings, list):
            print("unexpected format")
            return []

        for f in findings:
            f["file"] = filepath

        print(f"{len(findings)} issue(s) found")
        return findings

    except json.JSONDecodeError:
        print("parse error — model returned non-JSON")
        return []
    except Exception as e:
        print(f"error — {e}")
        return []


def analyze_codebase(processed_files):
    """
    Runs analysis across all files from the stripper.
    processed_files: dict { filepath: { 'content': str, 'findings': list } }
    Returns flat list of all findings.
    """
    all_findings = []
    files = list(processed_files.items())
    total = len(files)

    print(f"\nAnalyzing {total} file(s) with "
          f"{config.PROVIDER} / "
          f"{getattr(config, config.PROVIDER.upper() + '_MODEL', '')}...\n")

    for i, (filepath, data) in enumerate(files, 1):
        print(f"  [{i}/{total}]", end=" ")
        findings = analyze_file(filepath, data["content"])
        all_findings.extend(findings)

    print(f"\nScan complete. Total issues found: {len(all_findings)}")
    return all_findings