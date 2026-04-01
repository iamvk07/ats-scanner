"""
Keyword analysis engine.
Extracts, weights, and matches keywords between resume and job description.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Set


# ── SPECIAL REGEX PATTERNS ────────────────────────────────────────────────────
# Keywords that need custom regex instead of the default \b...\b pattern.
SPECIAL_PATTERNS = {
    "c": r"\bc(?![+#])\b",
    "c++": r"\bc\+\+",
    "c#": r"\bc#",
}

# ── KEYWORD TAXONOMY ──────────────────────────────────────────────────────────
# Weighted skill categories. Higher weight = more important for ATS matching.

SKILL_TAXONOMY = {
    "languages": {
        "weight": 10,
        "keywords": [
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "c#",
            "c",
            "go",
            "golang",
            "rust",
            "kotlin",
            "swift",
            "ruby",
            "php",
            "scala",
            "r",
            "matlab",
            "perl",
            "bash",
            "shell",
            "powershell",
            "sql",
            "html",
            "css",
            "sass",
            "less",
            "dart",
        ],
    },
    "frameworks": {
        "weight": 9,
        "keywords": [
            "react",
            "angular",
            "vue",
            "next.js",
            "nextjs",
            "nuxt",
            "svelte",
            "node.js",
            "nodejs",
            "express",
            "fastapi",
            "flask",
            "django",
            "spring",
            "spring boot",
            "hibernate",
            "rails",
            "laravel",
            "asp.net",
            ".net",
            "dotnet",
            "tensorflow",
            "pytorch",
            "keras",
            "pandas",
            "numpy",
            "scikit-learn",
            "sklearn",
            "matplotlib",
            "junit",
            "pytest",
            "jest",
            "mocha",
            "cypress",
            "selenium",
            "graphql",
            "rest",
            "grpc",
            "material-ui",
            "tailwind",
            "bootstrap",
            "jquery",
            "redux",
        ],
    },
    "databases": {
        "weight": 8,
        "keywords": [
            "postgresql",
            "postgres",
            "mysql",
            "sqlite",
            "mongodb",
            "redis",
            "elasticsearch",
            "cassandra",
            "dynamodb",
            "oracle",
            "sql server",
            "mssql",
            "mariadb",
            "firebase",
            "supabase",
            "nosql",
            "influxdb",
            "neo4j",
        ],
    },
    "devops_cloud": {
        "weight": 8,
        "keywords": [
            "docker",
            "kubernetes",
            "k8s",
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "terraform",
            "ansible",
            "jenkins",
            "github actions",
            "gitlab ci",
            "circleci",
            "travis",
            "ci/cd",
            "devops",
            "linux",
            "unix",
            "nginx",
            "apache",
            "microservices",
            "serverless",
            "lambda",
            "s3",
            "ec2",
            "rds",
            "cloudformation",
            "helm",
        ],
    },
    "tools": {
        "weight": 7,
        "keywords": [
            "git",
            "github",
            "gitlab",
            "bitbucket",
            "jira",
            "confluence",
            "slack",
            "figma",
            "postman",
            "swagger",
            "maven",
            "gradle",
            "npm",
            "yarn",
            "webpack",
            "vite",
            "vs code",
            "intellij",
            "android studio",
            "xcode",
            "vim",
        ],
    },
    "concepts": {
        "weight": 7,
        "keywords": [
            "agile",
            "scrum",
            "kanban",
            "tdd",
            "bdd",
            "oop",
            "object oriented",
            "functional programming",
            "data structures",
            "algorithms",
            "design patterns",
            "solid",
            "mvc",
            "mvvm",
            "api",
            "rest api",
            "restful",
            "websocket",
            "authentication",
            "authorization",
            "oauth",
            "jwt",
            "machine learning",
            "deep learning",
            "nlp",
            "computer vision",
            "data science",
            "big data",
            "etl",
            "data pipeline",
            "unit testing",
            "integration testing",
            "test driven",
            "code review",
            "debugging",
            "performance optimization",
            "security",
            "encryption",
            "version control",
        ],
    },
    "soft_skills": {
        "weight": 4,
        "keywords": [
            "communication",
            "teamwork",
            "collaboration",
            "leadership",
            "problem solving",
            "problem-solving",
            "analytical",
            "detail oriented",
            "fast learner",
            "self motivated",
            "adaptable",
            "creative",
            "critical thinking",
            "time management",
            "multitasking",
            "initiative",
            "proactive",
            "organized",
            "attention to detail",
        ],
    },
    "education": {
        "weight": 5,
        "keywords": [
            "bachelor",
            "master",
            "phd",
            "computer science",
            "software engineering",
            "information technology",
            "computer engineering",
            "mathematics",
            "statistics",
            "electrical engineering",
            "degree",
            "diploma",
            "certification",
            "bootcamp",
        ],
    },
}

# Common words to ignore
STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "must",
    "about",
    "this",
    "that",
    "these",
    "those",
    "we",
    "you",
    "they",
    "he",
    "she",
    "our",
    "your",
    "their",
    "its",
    "my",
    "all",
    "any",
    "some",
    "no",
    "not",
    "more",
    "most",
    "other",
    "such",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "each",
    "few",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "both",
    "only",
    "own",
    "same",
    "then",
    "when",
    "where",
    "who",
    "which",
    "how",
    "what",
    "why",
    "experience",
    "work",
    "working",
    "years",
    "year",
    "new",
    "using",
    "use",
    "used",
    "including",
    "include",
    "ability",
    "skills",
    "strong",
    "good",
    "great",
    "excellent",
    "knowledge",
    "understanding",
    "familiar",
}


def extract_keywords(text: str) -> Dict[str, List[str]]:
    """
    Extract keywords from text, organized by category.
    Returns dict of {category: [matched_keywords]}.
    """
    text_lower = text.lower()
    found = {}

    for category, data in SKILL_TAXONOMY.items():
        matches = []
        for kw in data["keywords"]:
            if kw in SPECIAL_PATTERNS:
                pattern = SPECIAL_PATTERNS[kw]
            else:
                pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower):
                matches.append(kw)
        if matches:
            found[category] = matches

    return found


def extract_ngrams(text: str, n: int = 2) -> List[str]:
    """Extract meaningful n-grams from text."""
    words = [
        w
        for w in re.findall(r"\b[a-z][a-z0-9\+#\.]*\b", text.lower())
        if w not in STOP_WORDS and len(w) > 2
    ]
    ngrams = []
    for i in range(len(words) - n + 1):
        ngrams.append(" ".join(words[i : i + n]))
    return ngrams


def get_word_frequencies(text: str) -> Counter:
    """Get frequency of meaningful words."""
    words = re.findall(r"\b[a-z][a-z0-9\+#\.]*\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return Counter(filtered)


def compute_match(resume_text: str, jd_text: str) -> Dict:
    """
    Core matching algorithm.
    Returns comprehensive match analysis.
    """
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    # Extract keywords from both
    jd_keywords = extract_keywords(jd_lower)
    resume_keywords = extract_keywords(resume_lower)

    # Flatten for comparison
    jd_flat = {kw for cats in jd_keywords.values() for kw in cats}
    resume_flat = {kw for cats in resume_keywords.values() for kw in cats}

    # Matched and missing
    matched = jd_flat & resume_flat
    missing = jd_flat - resume_flat

    # Weighted score
    total_weight = 0
    matched_weight = 0

    for category, data in SKILL_TAXONOMY.items():
        weight = data["weight"]
        jd_cat_kws = set(jd_keywords.get(category, []))
        resume_cat_kws = set(resume_keywords.get(category, []))

        if jd_cat_kws:
            cat_matched = jd_cat_kws & resume_cat_kws
            total_weight += len(jd_cat_kws) * weight
            matched_weight += len(cat_matched) * weight

    # Base score
    if total_weight > 0:
        weighted_score = (matched_weight / total_weight) * 100
    else:
        weighted_score = 0

    # Word frequency overlap bonus
    jd_freq = get_word_frequencies(jd_lower)
    resume_freq = get_word_frequencies(resume_lower)
    common_words = set(jd_freq.keys()) & set(resume_freq.keys())
    freq_bonus = min(10, len(common_words) * 0.3)

    final_score = min(99, weighted_score + freq_bonus)

    # Categorize matched/missing by category
    matched_by_cat = {}
    missing_by_cat = {}

    for category in SKILL_TAXONOMY:
        jd_cat = set(jd_keywords.get(category, []))
        resume_cat = set(resume_keywords.get(category, []))
        cat_matched = sorted(jd_cat & resume_cat)
        cat_missing = sorted(jd_cat - resume_cat)
        if cat_matched:
            matched_by_cat[category] = cat_matched
        if cat_missing:
            missing_by_cat[category] = cat_missing

    # Extract key phrases from JD not in resume
    jd_ngrams = set(extract_ngrams(jd_lower))
    resume_ngrams = set(extract_ngrams(resume_lower))
    missing_phrases = sorted(
        [
            p
            for p in jd_ngrams - resume_ngrams
            if not any(sw in p.split() for sw in STOP_WORDS)
        ],
        key=lambda x: jd_lower.count(x),
        reverse=True,
    )[:10]

    # Bonus skills in resume not in JD
    bonus_skills = sorted(resume_flat - jd_flat)

    # Grade
    grade = _score_to_grade(final_score)

    # Section analysis
    sections = _analyze_sections(resume_lower)

    return {
        "score": round(final_score, 1),
        "grade": grade,
        "matched_count": len(matched),
        "missing_count": len(missing),
        "total_jd_keywords": len(jd_flat),
        "matched_by_category": matched_by_cat,
        "missing_by_category": missing_by_cat,
        "missing_phrases": missing_phrases,
        "bonus_skills": bonus_skills[:15],
        "sections": sections,
        "jd_keyword_count": len(jd_flat),
        "resume_keyword_count": len(resume_flat),
    }


def _score_to_grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"


def _analyze_sections(resume_text: str) -> Dict[str, bool]:
    return {
        "contact": bool(re.search(r"email|phone|\@|\d{3}[-.\s]\d{3}", resume_text)),
        "education": bool(
            re.search(
                r"(?:^|\n)\s*(?:education|university|college|degree|bachelor|master)",
                resume_text,
            )
        ),
        "experience": bool(
            re.search(
                r"(?:^|\n)\s*(?:experience|work\s+history|employment|professional\s+experience)",
                resume_text,
            )
        ),
        "projects": bool(
            re.search(
                r"(?:^|\n)\s*(?:projects?|personal\s+projects?|academic\s+projects?)",
                resume_text,
            )
        ),
        "skills": bool(
            re.search(
                r"(?:^|\n)\s*(?:skills?|technical\s+skills?|core\s+competencies)",
                resume_text,
            )
        ),
        "summary": bool(
            re.search(
                r"(?:^|\n)\s*(?:summary|objective|professional\s+summary|profile|about\s+me)",
                resume_text,
            )
        ),
    }
