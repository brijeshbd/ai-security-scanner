# Contributing

Contributions are welcome — bug fixes, new features, new language support, or documentation improvements.

---

## Getting started

```bash
git clone https://github.com/YOUR_USERNAME/ai-security-scanner.git
cd ai-security-scanner
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Project layout

| File | What to change here |
|---|---|
| `config.py` | Add a new provider config key |
| `scanner/walker.py` | Add file extensions or skip folders |
| `scanner/stripper.py` | Add new secret patterns |
| `scanner/analyzer.py` | Add a new AI provider function |
| `scanner/reporter.py` | Change report layout or styling |

---

## Adding a new AI provider

1. Open `scanner/analyzer.py`
2. Add a function following this pattern:
   ```python
   def _call_myprovider(prompt):
       # import the SDK, call the API, return a string
       return response_text
   ```
3. Register it:
   ```python
   PROVIDERS = {
       ...
       "myprovider": _call_myprovider,
   }
   ```
4. Add config keys in `config.py`:
   ```python
   MYPROVIDER_API_KEY = os.getenv("MYPROVIDER_API_KEY", "")
   MYPROVIDER_MODEL   = "their-model-name"
   ```
5. Document it in `docs/providers.md`

---

## Adding secret patterns

Open `scanner/stripper.py` and add a tuple to `SECRET_PATTERNS`:

```python
("My Service Token",
 r'(myservice_[A-Za-z0-9]{32})'),
```

Test it by adding a fake token to `tests/test_stripper.py` and running the test.

---

## Running tests

```bash
python tests/test_walker.py
python tests/test_stripper.py
python tests/test_analyzer.py   # requires Ollama running locally
```

---

## Pull request checklist

- [ ] Tests pass locally
- [ ] New features have a test in `tests/`
- [ ] New providers are documented in `docs/providers.md`
- [ ] No real API keys or secrets committed