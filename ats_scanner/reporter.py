"""
Report generator.
Produces clean, readable terminal reports and optional file output.
"""

import os
import json
from datetime import datetime
from typing import Dict


# ── TERMINAL COLORS ──────────────────────────────────────────────────────────


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Bright variants
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    BRIGHT_RED = "\033[91m"


C = Color


def _supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    return (hasattr(os, "isatty") and os.isatty(1)) or os.environ.get("FORCE_COLOR")


USE_COLOR = _supports_color()


def col(text: str, *codes: str) -> str:
    if not USE_COLOR:
        return text
    return "".join(codes) + str(text) + C.RESET


def bold(text: str) -> str:
    return col(text, C.BOLD)


def dim(text: str) -> str:
    return col(text, C.DIM)


# ── LAYOUT HELPERS ───────────────────────────────────────────────────────────

WIDTH = 72


def line(char: str = "─", width: int = WIDTH) -> str:
    return col(char * width, C.DIM)


def header_line(char: str = "═", width: int = WIDTH) -> str:
    return col(char * width, C.CYAN)


def section_line(char: str = "─", width: int = WIDTH) -> str:
    return col(char * width, C.DIM)


def center(text: str, width: int = WIDTH) -> str:
    # Strip ANSI for length calculation
    import re

    clean = re.sub(r"\033\[[0-9;]*m", "", text)
    pad = max(0, (width - len(clean)) // 2)
    return " " * pad + text


def label(text: str, width: int = 20) -> str:
    return col(text.ljust(width), C.DIM)


# ── SCORE VISUALIZATION ──────────────────────────────────────────────────────


def score_bar(score: float, width: int = 40) -> str:
    filled = int((score / 100) * width)
    empty = width - filled

    if score >= 75:
        bar_color = C.BRIGHT_GREEN
    elif score >= 55:
        bar_color = C.BRIGHT_YELLOW
    else:
        bar_color = C.BRIGHT_RED

    bar = col("█" * filled, bar_color) + col("░" * empty, C.DIM)
    return f"[{bar}]"


def score_color(score: float) -> str:
    if score >= 75:
        return C.BRIGHT_GREEN
    if score >= 55:
        return C.BRIGHT_YELLOW
    return C.BRIGHT_RED


def grade_badge(grade: str) -> str:
    colors = {
        "A": (C.BG_GREEN, C.BOLD),
        "B": (C.BG_BLUE, C.BOLD),
        "C": (C.BG_YELLOW, C.BOLD),
        "D": (C.BG_RED, C.BOLD),
        "F": (C.BG_RED, C.BOLD),
    }
    bg, style = colors.get(grade, (C.BG_BLACK, C.BOLD))
    if USE_COLOR:
        return f"{bg}{style} {grade} {C.RESET}"
    return f"[{grade}]"


# ── KEYWORD TAGS ─────────────────────────────────────────────────────────────


def tag_matched(kw: str) -> str:
    return col(f" ✓ {kw} ", C.BRIGHT_GREEN)


def tag_missing(kw: str) -> str:
    return col(f" ✗ {kw} ", C.BRIGHT_RED)


def tag_bonus(kw: str) -> str:
    return col(f" + {kw} ", C.BRIGHT_BLUE)


def wrap_tags(tags: list, width: int = WIDTH - 4) -> list:
    """Wrap tag list into lines that fit within width."""
    import re

    lines = []
    current = "  "
    for tag in tags:
        clean = re.sub(r"\033\[[0-9;]*m", "", tag)
        if len(re.sub(r"\033\[[0-9;]*m", "", current)) + len(clean) > width:
            lines.append(current)
            current = "  " + tag
        else:
            current += tag
    if current.strip():
        lines.append(current)
    return lines


# ── CATEGORY DISPLAY NAMES ───────────────────────────────────────────────────

CAT_DISPLAY = {
    "languages": ("💻", "Programming Languages"),
    "frameworks": ("⚙️ ", "Frameworks & Libraries"),
    "databases": ("🗄️ ", "Databases"),
    "devops_cloud": ("☁️ ", "DevOps & Cloud"),
    "tools": ("🔧", "Tools & Platforms"),
    "concepts": ("🧠", "Concepts & Practices"),
    "soft_skills": ("🤝", "Soft Skills"),
    "education": ("🎓", "Education"),
}


# ── MAIN REPORT ──────────────────────────────────────────────────────────────


def print_report(
    result: Dict, resume_name: str = "resume", jd_name: str = "job description"
) -> None:
    score = result["score"]
    grade = result["grade"]
    lines = []

    def p(text: str = "") -> None:
        print(text)
        lines.append(text)

    # ── HEADER ──
    p()
    p(header_line("═"))
    p(center(col("  ATS SCANNER  ", C.BOLD, C.BRIGHT_CYAN)))
    p(center(col("Resume vs Job Description Analyzer", C.DIM)))
    p(center(col(f"by calebe94  ·  github.com/Calebe94/ats-scanner", C.DIM)))
    p(header_line("═"))
    p()

    # ── FILES ──
    p(f"  {label('Resume:')}  {col(resume_name, C.BRIGHT_WHITE)}")
    p(f"  {label('Job Description:')}  {col(jd_name, C.BRIGHT_WHITE)}")
    p(
        f"  {label('Analyzed:')}  {col(datetime.now().strftime('%Y-%m-%d %H:%M'), C.DIM)}"
    )
    p()

    # ── SCORE CARD ──
    p(section_line())
    p(f"  {bold('MATCH SCORE')}")
    p(section_line())
    p()

    score_str = col(f"{score:.1f}%", score_color(score), C.BOLD)
    p(f"  {score_str}  {score_bar(score)}  {grade_badge(grade)}")
    p()

    # Score interpretation
    if score >= 85:
        msg = col(
            "  ✦ Excellent match — strong candidate for this role", C.BRIGHT_GREEN
        )
    elif score >= 75:
        msg = col("  ✦ Good match — a few gaps to address", C.BRIGHT_GREEN)
    elif score >= 60:
        msg = col(
            "  ◈ Moderate match — worth applying but tailor your resume",
            C.BRIGHT_YELLOW,
        )
    elif score >= 45:
        msg = col("  ◈ Weak match — significant keyword gaps found", C.BRIGHT_YELLOW)
    else:
        msg = col(
            "  ✗ Poor match — consider different roles or major resume revision",
            C.BRIGHT_RED,
        )
    p(msg)
    p()

    # Quick stats
    p(
        f"  {label('JD Keywords Found:')}  {col(str(result['total_jd_keywords']), C.BRIGHT_WHITE)}"
    )
    p(
        f"  {label('Matched:')}  {col(str(result['matched_count']), C.BRIGHT_GREEN)}  "
        f"{label('Missing:')}  {col(str(result['missing_count']), C.BRIGHT_RED)}"
    )
    p()

    # ── MATCHED KEYWORDS ──
    if result["matched_by_category"]:
        p(section_line())
        matched_note = col(f"({result['matched_count']} found in your resume)", C.DIM)
        p(f"  {bold(col('✓ MATCHED KEYWORDS', C.BRIGHT_GREEN))}  {matched_note}")
        p(section_line())
        p()

        for cat, keywords in result["matched_by_category"].items():
            icon, name = CAT_DISPLAY.get(cat, ("·", cat.replace("_", " ").title()))
            p(f"  {icon}  {col(name, C.BOLD)}")
            tag_list = [tag_matched(k) for k in keywords]
            for tl in wrap_tags(tag_list):
                p(tl)
            p()

    # ── MISSING KEYWORDS ──
    if result["missing_by_category"]:
        p(section_line())
        missing_note = col(
            f"({result['missing_count']} not found in your resume)", C.DIM
        )
        p(f"  {bold(col('✗ MISSING KEYWORDS', C.BRIGHT_RED))}  {missing_note}")
        p(section_line())
        p()
        p(col("  Add these to your resume where applicable:", C.DIM))
        p()

        for cat, keywords in result["missing_by_category"].items():
            icon, name = CAT_DISPLAY.get(cat, ("·", cat.replace("_", " ").title()))
            p(f"  {icon}  {col(name, C.BOLD)}")
            tag_list = [tag_missing(k) for k in keywords]
            for tl in wrap_tags(tag_list):
                p(tl)
            p()

    # ── MISSING PHRASES ──
    if result["missing_phrases"]:
        p(section_line())
        p(f"  {bold(col('◈ KEY PHRASES FROM JD NOT IN RESUME', C.BRIGHT_YELLOW))}")
        p(section_line())
        p()
        p(col("  Consider naturally incorporating these phrases:", C.DIM))
        p()
        for phrase in result["missing_phrases"][:8]:
            p(f"    {col('→', C.BRIGHT_YELLOW)}  {phrase}")
        p()

    # ── DYNAMIC JD KEYWORDS ──
    dynamic_missing = result.get("dynamic_missing", [])
    dynamic_matched = result.get("dynamic_matched", [])
    if dynamic_missing or dynamic_matched:
        p(section_line())
        p(f"  {bold(col('⚡ ADDITIONAL JD REQUIREMENTS', C.BRIGHT_YELLOW))}")
        p(section_line())
        p()
        p(col("  Terms from the JD not in our standard taxonomy:", C.DIM))
        p()
        for kw in dynamic_matched[:10]:
            p(f"    {col('✓', C.BRIGHT_GREEN)}  {kw}  ({col('found', C.BRIGHT_GREEN)})")
        for kw in dynamic_missing[:10]:
            p(f"    {col('✗', C.BRIGHT_RED)}  {kw}  ({col('missing', C.BRIGHT_RED)})")
        p()

    # ── BONUS SKILLS ──
    if result["bonus_skills"]:
        p(section_line())
        bonus_note = col("(in your resume but not required by JD)", C.DIM)
        p(f"  {bold(col('+ BONUS SKILLS', C.BRIGHT_BLUE))}  {bonus_note}")
        p(section_line())
        p()
        tag_list = [tag_bonus(k) for k in result["bonus_skills"]]
        for tl in wrap_tags(tag_list):
            p(tl)
        p()

    # ── YEARS OF EXPERIENCE ──
    yoe_reqs = result.get("yoe_requirements", [])
    resume_yoe = result.get("resume_yoe", {})
    if yoe_reqs:
        p(section_line())
        p(f"  {bold('YEARS OF EXPERIENCE CHECK')}")
        p(section_line())
        p()
        if resume_yoe.get("has_dates"):
            p(f"  {label('Estimated YoE:')}  {col(f'~{resume_yoe[\"total_years\"]} years', C.BRIGHT_WHITE)}")
        else:
            p(f"  {label('Estimated YoE:')}  {col('Could not detect date ranges', C.BRIGHT_YELLOW)}")
        p()
        for req in yoe_reqs:
            skill_str = f" of {req['skill']}" if req.get("skill") else ""
            req_str = f"{req['years']}+ years{skill_str}"
            if resume_yoe.get("has_dates") and resume_yoe["total_years"] >= req["years"]:
                p(f"    {col('PASS', C.BRIGHT_GREEN)}  {req_str}")
            else:
                p(f"    {col('WARN', C.BRIGHT_YELLOW)}  {req_str}")
        p()

    # ── RESUME SECTIONS ──
    p(section_line())
    p(f"  {bold('RESUME SECTION CHECK')}")
    p(section_line())
    p()

    sections = result["sections"]
    for section_name, present in sections.items():
        icon = col("✓", C.BRIGHT_GREEN) if present else col("✗", C.BRIGHT_RED)
        status = (
            col("Found", C.BRIGHT_GREEN)
            if present
            else col("Not detected", C.BRIGHT_RED)
        )
        p(f"    {icon}  {section_name.capitalize().ljust(15)}  {status}")
    p()

    # ── KEYWORD DENSITY ──
    density = result.get("keyword_density", {})
    if density.get("total_words", 0) > 0:
        p(section_line())
        p(f"  {bold('KEYWORD DENSITY')}")
        p(section_line())
        p()
        pct = density["density_pct"]
        if density["status"] == "good":
            color = C.BRIGHT_GREEN
            msg = "Healthy density"
        elif density["status"] == "warning":
            color = C.BRIGHT_YELLOW
            msg = "Slightly high — review for natural flow"
        else:
            color = C.BRIGHT_RED
            msg = "Too high — ATS may flag as keyword stuffing"
        p(f"  {label('Density:')}  {col(f'{pct}%', color)}  ({msg})")
        p(f"  {label('Optimal range:')}  {col('2-3%', C.DIM)}")
        if density["stuffed_keywords"]:
            p()
            p(col("  Over-repeated keywords (>4 times):", C.BRIGHT_YELLOW))
            for item in density["stuffed_keywords"]:
                p(f"    {col('!', C.BRIGHT_YELLOW)}  {item['keyword']} ({item['count']}x)")
        p()

    # ── RECOMMENDATIONS ──
    p(section_line())
    p(f"  {bold('RECOMMENDATIONS')}")
    p(section_line())
    p()

    recs = _generate_recommendations(result)
    for i, rec in enumerate(recs, 1):
        p(f"  {col(str(i), C.BRIGHT_CYAN, C.BOLD)}.  {rec}")
        p()

    # ── FOOTER ──
    p(header_line("═"))
    p(center(col("ATS Scanner  ·  github.com/Calebe94/ats-scanner", C.DIM)))
    p(header_line("═"))
    p()

    return lines


def _generate_recommendations(result: Dict) -> list:
    """Generate context-aware, actionable recommendations using all analysis signals."""
    recs = []
    score = result["score"]
    missing = result["missing_by_category"]
    sections = result["sections"]
    density = result.get("keyword_density", {})
    yoe = result.get("yoe_requirements", [])
    resume_yoe = result.get("resume_yoe", {})
    dynamic_missing = result.get("dynamic_missing", [])
    keyword_placement = result.get("keyword_placement", {})

    if score < 50:
        recs.append(
            col("Critical: ", C.BRIGHT_RED, C.BOLD)
            + f"Your resume matches only {score:.0f}% of this JD. "
            "Focus on adding the top missing keywords from each category below."
        )

    for req in yoe:
        skill_str = f" of {req['skill']}" if req.get("skill") else ""
        if not resume_yoe.get("has_dates"):
            recs.append(
                col("Experience Dates: ", C.BRIGHT_YELLOW, C.BOLD)
                + f"The JD requires {req['years']}+ years{skill_str}. "
                "Add clear date ranges (e.g., 'Jan 2020 - Present') to your "
                "experience entries so ATS can verify tenure."
            )
            break
        elif resume_yoe["total_years"] < req["years"]:
            recs.append(
                col("Experience Gap: ", C.BRIGHT_YELLOW, C.BOLD)
                + f"The JD requires {req['years']}+ years{skill_str}, "
                f"but your resume shows ~{resume_yoe['total_years']} years. "
                "Consider including freelance work, internships, or relevant "
                "academic projects to bridge the gap."
            )

    for cat in ["languages", "frameworks", "databases", "devops_cloud"]:
        if missing.get(cat):
            kws = ", ".join(missing[cat][:3])
            cat_name = CAT_DISPLAY.get(cat, ("", cat))[1]
            recs.append(
                col(f"{cat_name}: ", C.BRIGHT_YELLOW, C.BOLD)
                + f"Missing {kws}. "
                + ("Add to your Skills section AND mention in Experience bullets "
                   "for maximum ATS weight." if not sections.get("skills")
                   else "Add these to your Skills section explicitly.")
            )

    if not sections.get("summary"):
        recs.append(
            col("Add a Summary: ", C.BRIGHT_BLUE, C.BOLD)
            + "A professional summary lets you front-load 4-6 core keywords "
            "from the JD. ATS systems weight summary keywords highly."
        )

    if not sections.get("skills"):
        recs.append(
            col("Add a Skills Section: ", C.BRIGHT_BLUE, C.BOLD)
            + "A dedicated Skills section gets a 1.5x weight multiplier in "
            "most ATS systems. List your technical skills explicitly."
        )

    if not sections.get("projects") and score < 75:
        recs.append(
            col("Add Projects: ", C.BRIGHT_BLUE, C.BOLD)
            + "A Projects section lets you demonstrate skills with context. "
            "'Built X using Python and React' scores higher than just listing them."
        )

    skills_kws = set(keyword_placement.get("skills", []))
    exp_kws = set(keyword_placement.get("experience", []))
    only_in_skills = skills_kws - exp_kws
    if only_in_skills and len(only_in_skills) > 2:
        kws = ", ".join(list(only_in_skills)[:3])
        recs.append(
            col("Prove Your Skills: ", C.BRIGHT_CYAN, C.BOLD)
            + f"{kws} appear only in your Skills list. "
            "Mention them in Experience bullets too — ATS rewards the "
            "'Claim + Proof' pattern (skill listed AND demonstrated)."
        )

    if density.get("status") == "danger":
        recs.append(
            col("Keyword Stuffing Alert: ", C.BRIGHT_RED, C.BOLD)
            + f"Your keyword density is {density['density_pct']}% (optimal: 2-3%). "
            "Modern ATS systems penalize over-repetition. Remove duplicate mentions."
        )
    elif density.get("stuffed_keywords"):
        stuffed = ", ".join(s["keyword"] for s in density["stuffed_keywords"][:3])
        recs.append(
            col("Repetition Warning: ", C.BRIGHT_YELLOW, C.BOLD)
            + f"{stuffed} appear more than 4 times. "
            "BM25 scoring saturates after 3-4 mentions — extra repetitions add zero value."
        )

    if dynamic_missing and len(dynamic_missing) > 2:
        kws = ", ".join(dynamic_missing[:3])
        recs.append(
            col("JD-Specific Terms: ", C.BRIGHT_YELLOW, C.BOLD)
            + f"The JD mentions {kws} which aren't standard taxonomy keywords. "
            "If you have experience with these, add them to your resume."
        )

    if score >= 85:
        recs.append(
            col("Excellent Match: ", C.BRIGHT_GREEN, C.BOLD)
            + "Strong alignment! Focus your cover letter on the 1-2 remaining "
            "gaps. Your resume should pass most ATS filters."
        )
    elif score >= 75:
        recs.append(
            col("Good Match: ", C.BRIGHT_GREEN, C.BOLD)
            + "Solid foundation. Address the missing keywords above and you'll "
            "be in the top tier of applicants for ATS scoring."
        )

    if not recs:
        recs.append(
            col("Well Optimized: ", C.BRIGHT_GREEN, C.BOLD)
            + "Your resume is well-aligned with this JD. "
            "Focus on quantifying achievements in your bullet points."
        )

    return recs


def save_report(result: Dict, output_path: str, resume_name: str, jd_name: str) -> None:
    """Save report as JSON for programmatic use."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "resume": resume_name,
        "job_description": jd_name,
        "score": result["score"],
        "grade": result["grade"],
        "matched_count": result["matched_count"],
        "missing_count": result["missing_count"],
        "matched_by_category": result["matched_by_category"],
        "missing_by_category": result["missing_by_category"],
        "missing_phrases": result["missing_phrases"],
        "bonus_skills": result["bonus_skills"],
        "sections": result["sections"],
        "recommendations": [
            r.replace("\033[0m", "")
            .replace("\033[1m", "")
            .replace("\033[91m", "")
            .replace("\033[92m", "")
            .replace("\033[93m", "")
            .replace("\033[94m", "")
            .replace("\033[95m", "")
            .replace("\033[96m", "")
            for r in _generate_recommendations(result)
        ],
    }

    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    else:
        # Plain text
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"ATS Scanner Report\n")
            f.write(f"Generated: {report['generated_at']}\n")
            f.write(f"Score: {result['score']}% (Grade {result['grade']})\n\n")
            f.write(f"Matched Keywords ({result['matched_count']}):\n")
            for cat, kws in result["matched_by_category"].items():
                f.write(f"  {cat}: {', '.join(kws)}\n")
            f.write(f"\nMissing Keywords ({result['missing_count']}):\n")
            for cat, kws in result["missing_by_category"].items():
                f.write(f"  {cat}: {', '.join(kws)}\n")

    print(
        f"\n  {col('✓', C.BRIGHT_GREEN)} Report saved to {col(output_path, C.BRIGHT_WHITE)}\n"
    )
