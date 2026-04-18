import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.analyzer import analyze_file

# This fake file has 4 deliberate vulnerabilities.
# See if Mistral can spot them all.
VULNERABLE_CODE = """
import sqlite3
import subprocess
import pickle

def get_user(username):
    conn = sqlite3.connect("users.db")
    # VULNERABILITY 1: SQL Injection — user input directly in query
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return conn.execute(query).fetchall()

def run_report(filename):
    # VULNERABILITY 2: Command Injection — user input passed to shell
    os.system("generate_report.sh " + filename)

def load_session(session_data):
    # VULNERABILITY 3: Insecure deserialization — pickle on untrusted data
    return pickle.loads(session_data)

def login(username, password):
    # VULNERABILITY 4: Hardcoded admin backdoor
    if username == "admin" and password == "letmein123":
        return True
    return check_db(username, password)
"""

# Write the fake file temporarily so analyzer can reference it
test_path = "/tmp/vulnerable_test.py"
with open(test_path, "w") as f:
    f.write(VULNERABLE_CODE)

print("Sending to Mistral for analysis...\n")
findings = analyze_file(test_path, VULNERABLE_CODE)

print(f"\n{'='*50}")
print(f"FINDINGS ({len(findings)} total):")
print('='*50)

for finding in findings:
    severity_colors = {
        "CRITICAL": "\033[91m",  # red
        "HIGH":     "\033[93m",  # yellow
        "MEDIUM":   "\033[94m",  # blue
        "LOW":      "\033[92m",  # green
    }
    reset = "\033[0m"
    color = severity_colors.get(finding.get("severity", ""), "")

    print(f"\n{color}[{finding.get('severity')}]{reset} {finding.get('type')}")
    print(f"  Line       : {finding.get('line')}")
    print(f"  Description: {finding.get('description')}")
    print(f"  Risk       : {finding.get('risk')}")
    print(f"  Fix        : {finding.get('fix')}")