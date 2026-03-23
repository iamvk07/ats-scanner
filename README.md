# ATS Scanner 🎯

A command-line tool that analyzes how well your resume matches a job description — the same way Applicant Tracking Systems (ATS) do.

**Zero external dependencies. Pure Python 3.8+.**

```
   _  _____ ____   ____
  / \|_   _/ ___| / ___|  ___  __ _ _ __  _ __   ___ _ __
 / _ \ | | \___ \| |  _ / __|/ _` | '_ \| '_ \ / _ \ '__|
/ ___ \| |  ___) | |_| |\__ \ (_| | | | | | | |  __/ |
/_/   \_\_| |____/ \____||___/\__,_|_| |_|_| |_|\___|_|
```

## What it does

Paste your resume and a job description — ATS Scanner tells you:

- 📊 **Match Score** (0–100%) with letter grade
- ✅ **Matched Keywords** — what you have that the JD wants
- ❌ **Missing Keywords** — what you're lacking, by category
- 💡 **Recommendations** — actionable suggestions to improve your score
- 🔍 **Key Phrases** — important phrases from the JD not in your resume
- ⭐ **Bonus Skills** — skills you have beyond what's required
- 📋 **Resume Section Check** — detects missing sections

## Demo

```bash
python scan.py --demo
```

Output:
```
═══════════════════════════════════════════════════════════════════════
                         ATS SCANNER
                Resume vs Job Description Analyzer
               by Vedant Kadam · github.com/iamvk07

  Resume:            demo_resume.txt
  Job Description:   demo_job_description.txt
  Analyzed:          2026-03-20 14:32

  MATCH SCORE
  ─────────────────────────────────────────────────────────────────────
  78.4%  [████████████████████████████░░░░░░░░░░░░]  [B]

  ✦ Good match — a few gaps to address

  Matched:  18     Missing:  4
```

## Installation

No installation needed. Just clone and run:

```bash
git clone https://github.com/iamvk07/ats-scanner
cd ats-scanner
python scan.py --help
```

**Requires Python 3.8+** — check with `python --version`

## Usage

### With files
```bash
# .txt files (recommended)
python scan.py --resume resume.txt --jd job_description.txt

# .pdf files (basic support)
python scan.py --resume resume.pdf --jd job.txt

# Save report to JSON
python scan.py --resume resume.txt --jd job.txt --output report.json
```

### Interactive mode (no files needed)
```bash
python scan.py
# Prompts you to paste resume text, then job description text
```

### Score only (for scripting)
```bash
python scan.py --resume resume.txt --jd job.txt --score-only
# Outputs: 78.4
```

### Demo with sample data
```bash
python scan.py --demo
```

## All Options

```
--resume,  -r    Path to resume (.txt or .pdf)
--jd,      -j    Path to job description (.txt or .pdf)
--output,  -o    Save report as .txt or .json
--score-only,-s  Print score number only
--no-color       Disable colored output
--demo           Run with built-in demo data
--version, -v    Show version
--help,    -h    Show help
```

## How It Works

1. **Extract** — reads text from .txt/.pdf files or direct input
2. **Tokenize** — cleans and normalizes text
3. **Match** — compares against a taxonomy of 200+ tech keywords across 8 categories
4. **Weight** — assigns category weights (languages: 10, frameworks: 9, databases: 8...)
5. **Score** — calculates weighted match percentage + frequency bonus
6. **Report** — generates detailed terminal report with recommendations

### Keyword Categories

| Category | Weight | Examples |
|----------|--------|---------|
| Programming Languages | 10 | Python, Java, JavaScript, C++ |
| Frameworks & Libraries | 9 | React, Flask, Spring, TensorFlow |
| Databases | 8 | PostgreSQL, MongoDB, Redis |
| DevOps & Cloud | 8 | Docker, AWS, GitHub Actions |
| Tools & Platforms | 7 | Git, Jira, VS Code |
| Concepts & Practices | 7 | Agile, CI/CD, REST API, OOP |
| Education | 5 | Computer Science, Bachelor's |
| Soft Skills | 4 | Communication, Leadership |

## Project Structure

```
ats-scanner/
├── scan.py                    # Entry point
├── ats_scanner/
│   ├── __init__.py
│   ├── cli.py                 # CLI argument parsing & interactive mode
│   ├── extractor.py           # Text extraction (.txt, .pdf, raw)
│   ├── analyzer.py            # Core keyword matching engine
│   └── reporter.py            # Terminal report generation
├── tests/
│   └── test_analyzer.py       # Unit tests (25 test cases)
├── sample_data/
│   ├── sample_resume.txt      # Example resume
│   └── sample_job.txt         # Example job description
├── requirements.txt           # Zero dependencies!
└── README.md
```

## Running Tests

```bash
# Using unittest (built-in, no install needed)
python -m unittest discover tests/ -v

# Using pytest (if installed)
pytest tests/ -v
```

## Why Zero Dependencies?

Most Python CLI tools require installing packages like `click`, `rich`, or `colorama`. ATS Scanner uses only the Python standard library — which means:

- ✅ Works anywhere Python is installed
- ✅ No `pip install` needed
- ✅ No version conflicts
- ✅ Runs on any OS (Windows, Mac, Linux)

## Limitations

- PDF extraction works on text-based PDFs. For scanned/image PDFs, copy text to a .txt file.
- Keyword matching is lexical — does not understand semantic similarity.
- Results are a guide, not a guarantee. ATS systems vary widely.

## Author

**Vedant Kadam** — CS Student @ University of New Brunswick

- GitHub: [github.com/iamvk07](https://github.com/iamvk07)
- LinkedIn: [linkedin.com/in/vedantkadam07](https://linkedin.com/in/vedantkadam07)

## License

MIT License — free to use, modify, and distribute.
