"""
CLI interface for ATS Scanner.
Usage: python scan.py --resume <file> --jd <file>
"""

import sys
import os
import argparse
import textwrap
from typing import Optional

from ats_scanner.extractor import extract_text, clean_text
from ats_scanner.analyzer import compute_match
from ats_scanner.reporter import (
    print_report,
    save_report,
    col,
    Color as C,
    bold,
    header_line,
    center,
)


BANNER = r"""
   _  _____ ____   ____
  / \|_   _/ ___| / ___|  ___  __ _ _ __  _ __   ___ _ __
 / _ \ | | \___ \| |  _ / __|/ _` | '_ \| '_ \ / _ \ '__|
/ ___ \| |  ___) | |_| |\__ \ (_| | | | | | | |  __/ |
/_/   \_\_| |____/ \____||___/\__,_|_| |_|_| |_|\___|_|
"""


def print_banner() -> None:
    if os.isatty(1):
        print(col(BANNER, C.BRIGHT_CYAN))
    print(col("  Resume vs Job Description ATS Keyword Analyzer", C.DIM))
    print(col("  github.com/Calebe94/ats-scanner\n", C.DIM))


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ats-scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            ATS Scanner — Analyze how well your resume matches a job description.

            Supports .txt, .pdf, .tex, and .docx files, or paste text directly.

            Examples:
              python scan.py --resume resume.txt --jd job.txt
              python scan.py --resume resume.pdf --jd job.txt --output report.json
              python scan.py --resume resume.txt --jd job.txt --score-only
        """),
        epilog="Built by calebe94 · github.com/Calebe94/ats-scanner",
    )

    parser.add_argument(
        "--resume",
        "-r",
        required=False,
        help="Path to your resume (.txt, .pdf, .tex, or .docx)",
    )
    parser.add_argument(
        "--jd",
        "-j",
        required=False,
        help="Path to job description (.txt, .pdf, .tex, or .docx)",
    )
    parser.add_argument(
        "--output", "-o", required=False, help="Save report to file (.txt or .json)"
    )
    parser.add_argument(
        "--score-only",
        "-s",
        action="store_true",
        help="Print only the score number (useful for scripting)",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run with built-in demo data"
    )
    parser.add_argument("--version", "-v", action="version", version="%(prog)s 1.0.0")

    return parser.parse_args(argv)


def get_input_interactive(prompt: str, label: str) -> str:
    """Get multiline text input interactively."""
    print(col(f"\n  {label}", C.BRIGHT_CYAN, C.BOLD))
    print(col("  Paste text below. Enter a blank line when done:", C.DIM))
    print(col("  " + "─" * 50, C.DIM))

    lines = []
    try:
        while True:
            line = input("  ")
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).strip()


def run_demo() -> None:
    """Run with built-in demo data."""
    demo_resume = """
    Edimar Calebe Castanho
    calebe94@pm.me | github.com/Calebe94 | Curitiba, PR

    EDUCATION
    Bachelor of Computer Science, University of New Brunswick, 2024-2028
    Minor in Mathematics

    EXPERIENCE
    Junior Software Developer - ParamShree Technologies (May 2023 - Dec 2023)
    - Developed web application features using HTML, CSS, JavaScript
    - Reduced post-deployment errors by writing unit tests
    - Collaborated in agile team, delivered sprint deliverables

    PROJECTS
    Flight Management System - Java, C++, Python, Flask, React, PostgreSQL
    - Built full-stack application with RESTful APIs
    - Designed normalized database schema
    - Implemented CI/CD pipeline with GitHub Actions

    Algorithm Visualizer - React, JavaScript
    - Built interactive sorting and graph traversal visualizer
    - BFS, DFS, Dijkstra algorithms

    CodeSense - JavaScript, Anthropic Claude API
    - AI-powered code review tool
    - REST API integration, JSON parsing

    SKILLS
    Languages: Java, Python, C++, JavaScript, SQL, HTML, CSS
    Frameworks: React, Flask, Node.js, FastAPI
    Tools: Git, Docker, GitHub Actions, PostgreSQL, VS Code
    Practices: Agile, Scrum, OOP, REST API, CI/CD, Unit Testing
    """

    demo_jd = """
    Software Developer Co-op
    We are looking for a motivated CS student to join our team.

    Requirements:
    - Experience with Python and JavaScript
    - Familiarity with React or similar frontend frameworks
    - Understanding of REST APIs and backend development
    - Experience with SQL databases (PostgreSQL, MySQL)
    - Knowledge of Git and version control
    - CI/CD pipeline experience (GitHub Actions, Jenkins)
    - Docker containerization experience
    - Agile/Scrum development practices
    - Strong object-oriented programming skills
    - Unit testing and debugging experience

    Nice to have:
    - TypeScript experience
    - AWS or cloud platform experience
    - Machine learning or AI integration experience
    - Node.js backend development

    We value:
    - Strong problem-solving skills
    - Team collaboration and communication
    - Fast learner who can adapt to new technologies
    """

    print(col("\n  Running demo analysis...\n", C.BRIGHT_YELLOW))
    resume_text = clean_text(demo_resume)
    jd_text = clean_text(demo_jd)
    result = compute_match(resume_text, jd_text, resume_raw=demo_resume, jd_raw=demo_jd)
    print_report(result, "demo_resume.txt", "demo_job_description.txt")


def main(argv=None) -> int:
    args = parse_args(argv)

    # Disable color if requested
    if args.no_color:
        import ats_scanner.reporter as reporter

        reporter.USE_COLOR = False

    # Print banner (unless score-only)
    if not args.score_only:
        print_banner()

    # Demo mode
    if args.demo:
        run_demo()
        return 0

    # Get resume text
    if args.resume:
        try:
            resume_raw = extract_text(args.resume)
            resume_name = os.path.basename(args.resume)
        except (ValueError, FileNotFoundError) as e:
            print(
                col(f"\n  Error reading resume: {e}\n", C.BRIGHT_RED), file=sys.stderr
            )
            return 1
    else:
        if args.score_only:
            print(
                col("Error: --resume required with --score-only", C.BRIGHT_RED),
                file=sys.stderr,
            )
            return 1
        resume_raw = get_input_interactive(
            "RESUME", "Step 1 of 2 — Paste your resume text"
        )
        resume_name = "pasted_resume"

    # Get JD text
    if args.jd:
        try:
            jd_raw = extract_text(args.jd)
            jd_name = os.path.basename(args.jd)
        except (ValueError, FileNotFoundError) as e:
            print(
                col(f"\n  Error reading job description: {e}\n", C.BRIGHT_RED),
                file=sys.stderr,
            )
            return 1
    else:
        if args.score_only:
            print(
                col("Error: --jd required with --score-only", C.BRIGHT_RED),
                file=sys.stderr,
            )
            return 1
        jd_raw = get_input_interactive(
            "JOB DESCRIPTION", "Step 2 of 2 — Paste the job description"
        )
        jd_name = "pasted_jd"

    if not resume_raw.strip():
        print(col("\n  Error: Resume text is empty.\n", C.BRIGHT_RED), file=sys.stderr)
        return 1

    if not jd_raw.strip():
        print(
            col("\n  Error: Job description text is empty.\n", C.BRIGHT_RED),
            file=sys.stderr,
        )
        return 1

    # Analyze
    if not args.score_only:
        print(col("\n  Analyzing...\n", C.DIM))

    resume_clean = clean_text(resume_raw)
    jd_clean = clean_text(jd_raw)
    result = compute_match(resume_clean, jd_clean, resume_raw=resume_raw, jd_raw=jd_raw)

    # Output
    if args.score_only:
        print(f"{result['score']:.1f}")
        return 0

    print_report(result, resume_name, jd_name)

    # Save if requested
    if args.output:
        try:
            save_report(result, args.output, resume_name, jd_name)
        except Exception as e:
            print(col(f"  Warning: Could not save report: {e}", C.BRIGHT_YELLOW))

    return 0


if __name__ == "__main__":
    sys.exit(main())
