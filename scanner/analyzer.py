import ollama
import json
import os

# This is the most important part of the whole project.
# The quality of security findings depends almost entirely
# on how well we instruct the model here.
#
# We tell it:
#  1. exactly what role to play
#  2. what categories to look for
#  3. precisely what format to return
#  4. to never make things up if unsure

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

For each vulnerability you find, you MUST respond ONLY with a valid JSON array.
Each item in the array must have exactly these fields:
{
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "type": "short vulnerability name, e.g. SQL Injection",
  "line": line number as integer or null if unknown,
  "description": "one sentence explaining what the vulnerability is",
  "risk": "one sentence explaining what an attacker could do if they exploited this",
  "fix": "concrete code fix or recommendation, be specific"
}

Rules:
- Return ONLY the JSON array. No intro text, no explanation, no markdown fences.
- If you find no vulnerabilities, return an empty array: []
- Do not invent vulnerabilities. Only report what you can clearly see in the code.
- Order findings by severity: CRITICAL first, then HIGH, MEDIUM, LOW.
"""


def build_user_prompt(filepath, content):
    """
    Wraps the code in a clear prompt so Mistral knows
    exactly what file it's looking at and what to do.
    """
    filename = os.path.basename(filepath)
    extension = os.path.splitext(filename)[1]

    return f"""Analyze this file for security vulnerabilities.

File: {filename}
Language: {extension}

Code:
{content}

Return your findings as a JSON array only."""


def analyze_file(filepath, cleaned_content, model="mistral"):
    """
    Sends one file's cleaned content to Mistral for analysis.
    Returns a list of finding dicts, or empty list if none found.
    """
    # Skip files that are basically empty — nothing to analyze
    if not cleaned_content or len(cleaned_content.strip()) < 10:
        return []

    # Very large files would exceed Mistral's context window.
    # We truncate to ~8000 chars (~2000 tokens) to stay safe.
    # In Phase 5 we'll handle large files properly with chunking.
    MAX_CHARS = 8000
    if len(cleaned_content) > MAX_CHARS:
        cleaned_content = cleaned_content[:MAX_CHARS]
        cleaned_content += "\n\n# [FILE TRUNCATED FOR ANALYSIS]"

    print(f"  Analyzing: {os.path.basename(filepath)}...", end=" ", flush=True)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(filepath, cleaned_content)},
            ],
            # These settings make output more focused and consistent.
            # temperature=0 means deterministic — same code = same findings every time.
            options={
                "temperature": 0,
                "num_predict": 2000,
            }
        )

        raw = response["message"]["content"].strip()

        # Sometimes models add markdown fences even when told not to.
        # Strip them defensively.
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        # If response is empty or model said nothing to report
        if not raw or raw == "[]":
            print("clean")
            return []

        findings = json.loads(raw)

        # Validate it's actually a list
        if not isinstance(findings, list):
            print("unexpected format")
            return []

        # Attach the filepath to each finding for the report later
        for f in findings:
            f["file"] = filepath

        print(f"{len(findings)} issue(s) found")
        return findings

    except json.JSONDecodeError:
        # Model didn't return valid JSON — happens occasionally
        # We'll handle this more gracefully in a future phase
        print("parse error (model returned non-JSON)")
        return []

    except Exception as e:
        print(f"error — {e}")
        return []


def analyze_codebase(processed_files, model="mistral"):
    """
    Runs analysis on all files returned by the stripper.
    
    processed_files: dict from stripper.process_files()
      { filepath: { 'content': ..., 'findings': [...] } }
    
    Returns a flat list of all security findings across all files.
    """
    all_findings = []
    files = list(processed_files.items())
    total = len(files)

    print(f"\nAnalyzing {total} file(s) with {model}...\n")

    for i, (filepath, data) in enumerate(files, 1):
        print(f"  [{i}/{total}]", end=" ")
        findings = analyze_file(filepath, data["content"], model)
        all_findings.extend(findings)

    print(f"\nScan complete. Total issues found: {len(all_findings)}")
    return all_findings