import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.stripper import strip_secrets

# Fake code that looks like a real project with exposed secrets
# None of these are real keys — just realistic-looking test data
FAKE_CODE = """
import os
import requests

# BAD: developer hardcoded credentials directly in source
API_KEY = "sk-abc123def456ghi789jkl012mno345pqr"
password = "supersecret123"
token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcd1234"

AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

DATABASE_URL = "postgresql://admin:myrealpassword@localhost/mydb"

def get_data():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig"}
    return requests.get("https://api.example.com", headers=headers)
"""

print("=" * 50)
print("ORIGINAL CODE:")
print("=" * 50)
print(FAKE_CODE)

cleaned, findings = strip_secrets(FAKE_CODE, "fake_config.py")

print("=" * 50)
print("AFTER SECRET STRIPPING:")
print("=" * 50)
print(cleaned)

print("=" * 50)
print(f"SECRETS FOUND: {len(findings)}")
print("=" * 50)
for f in findings:
    print(f"  Line {f['line']:3} — {f['type']}")