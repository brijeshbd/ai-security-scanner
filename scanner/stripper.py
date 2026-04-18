import re
import os

# Each tuple is: (human_readable_name, regex_pattern)
# The pattern always has a capture group around the SECRET VALUE ONLY
# so we can replace just the value, not the whole line.
#
# Why keep the whole line? Because "API_KEY=[REDACTED]" still tells
# the AI "there is an API key here" — which is useful security context.

SECRET_PATTERNS = [

    # --- Cloud provider keys ---
    ("AWS Access Key",
     r'(AKIA[0-9A-Z]{16})'),

    ("AWS Secret Key",
     r'(?i)(aws_secret_access_key\s*=\s*["\']?)([A-Za-z0-9/+=]{40})(["\']?)'),

    ("Google API Key",
     r'(AIza[0-9A-Za-z\-_]{35})'),

    ("Google OAuth",
     r'([0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com)'),

    # --- Source control tokens ---
    ("GitHub Token",
     r'(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})'),

    ("GitLab Token",
     r'(glpat-[A-Za-z0-9\-]{20})'),

    # --- Payment ---
    ("Stripe Secret Key",
     r'(sk_live_[0-9a-zA-Z]{24,})'),

    ("Stripe Publishable Key",
     r'(pk_live_[0-9a-zA-Z]{24,})'),

    # --- Communication services ---
    ("Twilio Account SID",
     r'(AC[a-zA-Z0-9]{32})'),

    ("Twilio Auth Token",
     r'(?i)(twilio.*?auth.*?token\s*=\s*["\']?)([a-zA-Z0-9]{32})(["\']?)'),

    ("SendGrid API Key",
     r'(SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43})'),

    # --- Generic patterns (most common in real projects) ---

    # Matches: API_KEY = "abc123secret"
    #          api_key: 'mysecretvalue'
    ("Generic API Key assignment",
     r'(?i)(api[_\-]?key\s*[=:]\s*["\']?)([A-Za-z0-9\-_]{16,})(["\']?)'),

    # Matches: password = "hunter2"
    #          PASSWORD: "supersecret"
    ("Password assignment",
     r'(?i)(password\s*[=:]\s*["\']?)([^\s"\']{6,})(["\']?)'),

    # Matches: secret = "abc..."
    #          SECRET_KEY = "xyz..."
    ("Secret assignment",
     r'(?i)(secret[_\-]?key?\s*[=:]\s*["\']?)([A-Za-z0-9\-_]{8,})(["\']?)'),

    # Matches: token = "eyJhbGci..."
    ("Token assignment",
     r'(?i)(token\s*[=:]\s*["\']?)([A-Za-z0-9\-_\.]{16,})(["\']?)'),

    # Matches: auth = "Bearer abc123..."
    ("Bearer token",
     r'(Bearer\s+)([A-Za-z0-9\-_\.]{16,})'),

    # JWT tokens — always 3 base64 parts separated by dots
    ("JWT Token",
     r'(eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)'),

    # .env file format: ANY_KEY=somevalue
    # This is a catch-all for .env files
    ("Env file value",
     r'(?m)^([A-Z][A-Z0-9_]{2,}\s*=\s*)([^\s#\n]{4,})'),

    # Database connection strings
    # Matches: postgresql://user:PASSWORD@host/db
    ("DB connection string password",
     r'(?i)((?:postgresql|mysql|mongodb|redis)://[^:]+:)([^@\s]+)(@)'),

    # Private key blocks (SSH, RSA, etc.)
    ("Private key block",
     r'(-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----)'),
]


def strip_secrets(content, filepath=""):
    """
    Takes file content as a string, returns (cleaned_content, list_of_findings).
    
    cleaned_content: the content with secrets replaced by [REDACTED]
    findings: list of dicts describing what was found and where
    """
    findings = []
    cleaned = content

    for name, pattern in SECRET_PATTERNS:
        matches = list(re.finditer(pattern, cleaned))
        
        for match in matches:
            # For patterns with 3 groups (prefix, SECRET, suffix)
            # we only redact the middle group (the actual secret value)
            # For patterns with 1 group (the whole thing is the secret)
            # we redact the whole match
            
            if match.lastindex and match.lastindex >= 2:
                # Multi-group pattern: keep prefix and suffix, redact middle
                original = match.group(0)
                prefix = match.group(1)
                suffix = match.group(match.lastindex) if match.lastindex >= 3 else ""
                redacted = f"{prefix}[REDACTED]{suffix}"
            else:
                # Single group or whole match is the secret
                original = match.group(0)
                redacted = "[REDACTED]"

            findings.append({
                'type': name,
                'line': content[:match.start()].count('\n') + 1,
                'file': filepath,
            })

            # Replace this specific occurrence in the content
            cleaned = cleaned.replace(original, redacted, 1)

    return cleaned, findings


def process_file(filepath):
    """
    Reads a file, strips secrets, returns cleaned content + findings.
    Returns None if the file can't be read.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"[WARN] Could not read {filepath}: {e}")
        return None, []

    cleaned, findings = strip_secrets(content, filepath)
    return cleaned, findings


def process_files(file_paths):
    """
    Processes a list of files.
    Returns a dict: { filepath: { 'content': ..., 'findings': [...] } }
    """
    results = {}
    total_secrets = 0

    for path in file_paths:
        cleaned, findings = process_file(path)
        if cleaned is not None:
            results[path] = {
                'content': cleaned,
                'findings': findings,
            }
            if findings:
                total_secrets += len(findings)
                print(f"  [!] {os.path.basename(path)} — "
                      f"{len(findings)} secret(s) found and redacted")

    if total_secrets == 0:
        print("  [OK] No secrets detected in any file")
    else:
        print(f"\n  Total secrets redacted: {total_secrets}")

    return results