# Setup Guide

This guide assumes you have never used Python or the terminal before. Follow each step in order.

---

## What you need before starting

- A computer running Mac, Windows, or Linux
- At least 8GB of RAM
- At least 5GB of free disk space
- An internet connection (only needed for initial setup)

---

## Step 1 — Check if Python is installed

Open your terminal:
- **Mac**: press `Cmd + Space`, type `Terminal`, press Enter
- **Windows**: press `Win + R`, type `cmd`, press Enter
- **Linux**: press `Ctrl + Alt + T`

Type this and press Enter:
```
python --version
```

You should see something like `Python 3.11.2`. Any version starting with 3.8 or higher is fine.

If you see `command not found`, download Python from https://python.org/downloads and install it. During installation on Windows, tick the box that says **"Add Python to PATH"**.

---

## Step 2 — Download the scanner

If you have Git installed:
```bash
git clone https://github.com/YOUR_USERNAME/ai-security-scanner.git
cd ai-security-scanner
```

If you don't have Git, click the green **Code** button on the GitHub page, choose **Download ZIP**, then unzip it and open a terminal in that folder.

---

## Step 3 — Create a virtual environment

A virtual environment is an isolated space for this project's software. It prevents conflicts with other Python programs on your computer.

```bash
python -m venv venv
```

Now activate it:

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)` at the start. This means you're inside the virtual environment. You need to do this activation step every time you open a new terminal window to use the scanner.

---

## Step 4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs two libraries: `ollama` (lets Python talk to the local AI) and `reportlab` (builds the PDF report). Takes about 60 seconds.

---

## Step 5 — Install Ollama

Ollama is the free software that runs an AI model on your own computer.

1. Go to **https://ollama.com/download**
2. Click the download button for your operating system
3. Install it like any normal app (drag to Applications on Mac, run the installer on Windows)

Verify it installed correctly:
```bash
ollama --version
```

You should see a version number.

---

## Step 6 — Download the AI model

This downloads Mistral, the AI model we use. It's a one-time download of about 4GB.

```bash
ollama pull mistral
```

This will take 5–15 minutes depending on your internet speed. You'll see a progress bar. Once done, verify it's ready:

```bash
ollama list
```

You should see `mistral:latest` in the list.

---

## Step 7 — Run your first scan

Make sure `(venv)` is showing in your terminal, then:

```bash
python main.py ./path/to/your/project
```

Replace `./path/to/your/project` with the actual path to the code you want to scan. For example:
- `python main.py ./my-website`
- `python main.py /Users/yourname/Documents/my-app`
- `python main.py .` (scans the current folder)

The scan takes 1–5 minutes depending on how many files your project has.

---

## Step 8 — Open the report

When the scan finishes, it will print something like:

```
Report saved: reports/scan_2026-04-18_14-32.pdf
```

Open that PDF file:

**Mac:**
```bash
open reports/scan_*.pdf
```

**Windows:**
```bash
start reports/scan_*.pdf
```

**Linux:**
```bash
xdg-open reports/scan_*.pdf
```

The PDF opens in your default PDF viewer (Preview on Mac, Edge or Adobe on Windows). You can also open it directly in Chrome or Firefox by dragging the file into the browser.

---

## Common problems

**"command not found: python"**
Try `python3` instead of `python`. If that works, replace `python` with `python3` in all commands.

**"(venv) disappeared from my terminal"**
You opened a new terminal window. Run the activate command again (Step 3).

**"ollama: command not found"**
Ollama isn't installed or wasn't added to your PATH. Re-install from https://ollama.com/download and restart your terminal.

**"No module named 'ollama'" or "No module named 'reportlab'"**
Your virtual environment is not active. Run `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows) first, then try again.

**Scan is very slow**
This is normal for the first scan — your computer is warming up the AI model. Subsequent scans on the same machine are faster.

**"No scannable files found"**
The path you provided might be wrong, or the project uses a language not yet in our list. Check the path and try again.

**PDF doesn't open**
Try dragging the `.pdf` file from the `reports/` folder directly into your browser (Chrome or Firefox work well).

---

## Updating the scanner

```bash
git pull
pip install -r requirements.txt
```