# ATS Scanner

A CLI + web tool that analyzes how well your resume matches a job description — the same way Applicant Tracking Systems (ATS) do.

**TypeScript monorepo. Shared core engine. Zero runtime dependencies for web.**

```
   _  _____ ____   ____
  / \|_   _/ ___| / ___|  ___  __ _ _ __  _ __   ___ _ __
 / _ \ | | \___ \| |  _ / __|/ _` | '_ \| '_ \ / _ \ '__|
/ ___ \| |  ___) | |_| |\__ \ (_| | | | | | | |  __/ |
/_/   \_\_| |____/ \____||___/\__,_|_| |_|_| |_|\___|_|
```

## What it does

Paste your resume and a job description — ATS Scanner tells you:

- **Match Score** (0-100%) with letter grade
- **Matched Keywords** — what you have that the JD wants
- **Missing Keywords** — what you're lacking, by category
- **Recommendations** — actionable suggestions to improve your score
- **Key Phrases** — important phrases from the JD not in your resume
- **Bonus Skills** — skills you have beyond what's required
- **Resume Section Check** — detects missing sections
- **Keyword Density** — flags over-repetition (BM25 saturation)
- **Years of Experience** — detects and validates YoE requirements

## Quick Start

```bash
# Clone and install
git clone https://github.com/Calebe94/ats-scanner
cd ats-scanner
pnpm install

# Run demo
pnpm --filter ats-scanner dev -- --demo

# Analyze files
pnpm --filter ats-scanner dev -- --resume resume.txt --jd job.txt

# Score only (for scripting)
pnpm --filter ats-scanner dev -- -r resume.txt -j job.txt -s
```

### Build and run

```bash
pnpm build
node apps/cli/dist/index.js --demo
node apps/cli/dist/index.js -r resume.txt -j job.txt
```

### Web app (development)

```bash
pnpm dev:web
```

### Web app (production build)

```bash
pnpm build
pnpm --filter web preview
```

## All CLI Options

```
--resume,  -r    Path to resume (.txt, .pdf, .tex, or .docx)
--jd,      -j    Path to job description (.txt, .pdf, .tex, or .docx)
--output,  -o    Save report as .txt or .json
--score-only,-s  Print score number only
--no-color       Disable colored output
--demo           Run with built-in demo data
--version, -v    Show version
--help,    -h    Show help
```

## How It Works

1. **Extract** — reads text from .txt/.pdf/.tex/.docx files or direct input
2. **Normalize** — resolves synonyms (k8s → kubernetes, js → javascript)
3. **Match** — compares against a taxonomy of 200+ tech keywords across 8 categories
4. **Weight** — section-aware scoring (Skills: 1.5x, Experience: 1.3x, Summary: 1.2x)
5. **Score** — combined formula: 70% taxonomy + 20% BM25 + 10% dynamic keywords
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
├── package.json                 # Root workspace config
├── pnpm-workspace.yaml          # Workspace definition
├── tsconfig.base.json           # Shared TS config
├── vitest.workspace.ts          # Test config
├── .github/workflows/           # CI/CD
│   ├── deploy.yml               # Build + deploy web to GitHub Pages
│   └── ci.yml                   # PR checks
├── packages/
│   └── core/                    # @ats-scanner/core (shared engine)
│       ├── src/
│       │   ├── index.ts         # Public API exports
│       │   ├── analyzer.ts      # Core matching engine
│       │   ├── extractor.ts     # Text extraction (clean, LaTeX strip)
│       │   ├── taxonomy.ts      # Keywords, synonyms, constants
│       │   └── types.ts         # TypeScript interfaces
│       └── __tests__/           # 92 unit tests
├── apps/
│   ├── cli/                     # ats-scanner CLI
│   │   └── src/
│   │       ├── index.ts         # Entry point
│   │       ├── cli.ts           # Commander.js args
│   │       ├── reporter.ts      # Terminal report
│   │       ├── extractor.ts     # Node.js file I/O
│   │       └── demo.ts          # Demo data
│   └── web/                     # Web application (Vite)
│       ├── index.html           # Shell HTML
│       └── src/
│           ├── main.ts          # Entry + event wiring
│           ├── scanner.ts       # UI ↔ core bridge
│           ├── ui.ts            # DOM rendering
│           ├── file-reader.ts   # Client-side file extraction
│           └── style.css        # Terminal aesthetic styles
└── sample_data/                 # Example files
```

## Running Tests

```bash
pnpm test
```

## Development

```bash
# Web app with HMR
pnpm dev:web

# CLI in dev mode
pnpm dev:cli -- --demo

# Build everything
pnpm build

# Typecheck
pnpm --filter @ats-scanner/core typecheck
```

## Limitations

- PDF extraction works on text-based PDFs. For scanned/image PDFs, copy text to a .txt file.
- LaTeX extraction strips common commands but may not fully resolve custom macros.
- DOCX extraction reads text content only — images, complex tables may not be captured.
- Keyword matching is lexical — does not understand semantic similarity.
- Results are a guide, not a guarantee. ATS systems vary widely.

## Author

**Edimar Calebe Castanho** (calebe94) — Computer Engineer

- GitHub: [github.com/Calebe94](https://github.com/Calebe94)
- Blog: [blog.calebe.dev.br](https://blog.calebe.dev.br)

## License

MIT License — free to use, modify, and distribute.
