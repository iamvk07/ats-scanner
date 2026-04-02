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

# ── SYNONYM / ALIAS MAP ──────────────────────────────────────────────────────
# Maps alternative names to their canonical form in SKILL_TAXONOMY.
# Aliases here must NOT also appear in SKILL_TAXONOMY (cleaned up in Step 0).
SYNONYM_MAP = {
    # Languages
    "js": "javascript",
    "es6": "javascript",
    "es7": "javascript",
    "ts": "typescript",
    "golang": "go",
    "c sharp": "c#",
    "csharp": "c#",
    "cplusplus": "c++",
    "py": "python",
    "rb": "ruby",
    # Frameworks
    "nextjs": "next.js",
    "nodejs": "node.js",
    "node": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "aspnet": "asp.net",
    "asp.net core": "asp.net",
    "dotnet": ".net",
    "dot net": ".net",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "material ui": "material-ui",
    "mui": "material-ui",
    "tailwindcss": "tailwind",
    "tailwind css": "tailwind",
    # Databases
    "postgres": "postgresql",
    "pg": "postgresql",
    "mongo": "mongodb",
    "elastic": "elasticsearch",
    "dynamo": "dynamodb",
    "ms sql": "sql server",
    "mssql": "sql server",
    "maria": "mariadb",
    # DevOps & Cloud
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "microsoft azure": "azure",
    "gh actions": "github actions",
    "github ci": "github actions",
    "gitlab cicd": "gitlab ci",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    # Tools
    "visual studio code": "vs code",
    "vscode": "vs code",
    # Concepts
    "object oriented programming": "oop",
    "object-oriented": "oop",
    "object oriented": "oop",
    "test driven development": "tdd",
    "test-driven development": "tdd",
    "behavior driven development": "bdd",
    "behavior-driven development": "bdd",
    "representational state transfer": "rest",
    "restful api": "rest api",
    "restful": "rest api",
    "json web token": "jwt",
    "json web tokens": "jwt",
    "natural language processing": "nlp",
    "ml": "machine learning",
    "dl": "deep learning",
    "cv": "computer vision",
    "ds": "data science",
    # Soft Skills
    "problem solving": "problem-solving",
    "detail-oriented": "detail oriented",
    "self-motivated": "self motivated",
}

# Pre-sorted by alias length descending so multi-word aliases are replaced first
_SORTED_SYNONYMS = sorted(SYNONYM_MAP.items(), key=lambda x: -len(x[0]))


def normalize_text(text: str) -> str:
    """
    Replace known synonyms/aliases with their canonical taxonomy form.
    Expects already-lowercased input. Processes longer aliases first
    to avoid partial replacements (e.g., 'amazon web services' before 'aws').
    """
    result = text
    for alias, canonical in _SORTED_SYNONYMS:
        pattern = r"\b" + re.escape(alias) + r"\b"
        result = re.sub(pattern, canonical, result)
    return result


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
            "nuxt",
            "svelte",
            "node.js",
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
            "tensorflow",
            "pytorch",
            "keras",
            "pandas",
            "numpy",
            "scikit-learn",
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
            "mysql",
            "sqlite",
            "mongodb",
            "redis",
            "elasticsearch",
            "cassandra",
            "dynamodb",
            "oracle",
            "sql server",
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
            "aws",
            "azure",
            "gcp",
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
            "functional programming",
            "data structures",
            "algorithms",
            "design patterns",
            "solid",
            "mvc",
            "mvvm",
            "api",
            "rest api",
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


# ── DYNAMIC JD KEYWORD EXTRACTION ────────────────────────────────────────────

REQUIREMENT_SIGNALS = re.compile(
    r"(?:experience\s+(?:with|in|using)|"
    r"proficien(?:t|cy)\s+(?:with|in)|"
    r"knowledge\s+of|"
    r"familiar(?:ity)?\s+with|"
    r"expertise\s+(?:in|with)|"
    r"(?:must|should)\s+(?:have|know)|"
    r"required|preferred|nice\s+to\s+have|"
    r"skills?\s*:)"
    r"\s+(.+?)(?:\.|,|;|\n|$)",
    re.IGNORECASE,
)

BULLET_PATTERN = re.compile(r"(?:^|\n)\s*(?:[-*+]|\d+[.)]\s)\s*(.+?)(?:\n|$)")


def extract_dynamic_keywords(jd_text: str, taxonomy_keywords: Set[str]) -> List[str]:
    """
    Extract potential skill keywords from JD text that are NOT in the
    static taxonomy. Uses requirement contexts, capitalized terms, and
    bullet points as signals.
    """
    candidates = set()

    # 1. Terms from requirement signal contexts
    for match in REQUIREMENT_SIGNALS.finditer(jd_text):
        phrase = match.group(1).strip()
        for term in re.split(r",\s*|\s+and\s+|\s+or\s+", phrase):
            term = term.strip().lower()
            term = re.sub(r"[^\w\s\+#\.\-]", "", term).strip()
            if (
                len(term) > 2
                and term not in STOP_WORDS
                and term not in taxonomy_keywords
            ):
                candidates.add(term)

    # 2. Capitalized terms (proper nouns / tool names) from original text
    cap_pattern = re.compile(r"\b([A-Z][a-zA-Z0-9\+#\.]*(?:\s+[A-Z][a-zA-Z0-9]*)*)\b")
    for match in cap_pattern.finditer(jd_text):
        term = match.group(1).strip()
        term_lower = term.lower()
        pos = match.start()
        is_sentence_start = (
            pos == 0
            or jd_text[pos - 1] in ".!?\n"
            or (pos >= 2 and jd_text[pos - 2 : pos] in ". ")
        )
        if (
            len(term_lower) > 2
            and term_lower not in STOP_WORDS
            and term_lower not in taxonomy_keywords
            and not is_sentence_start
        ):
            candidates.add(term_lower)

    # 3. Terms from bullet points
    for match in BULLET_PATTERN.finditer(jd_text):
        line = match.group(1).strip()
        words = [w.strip().lower() for w in re.split(r",\s*|\s+and\s+", line)]
        for w in words:
            w = re.sub(r"[^\w\s\+#\.\-]", "", w).strip()
            if (
                len(w) > 2
                and w not in STOP_WORDS
                and w not in taxonomy_keywords
                and len(w.split()) <= 3
            ):
                candidates.add(w)

    return sorted(candidates)


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


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Compute Jaccard similarity between two texts based on meaningful words.
    Returns 0.0-1.0 where 1.0 means identical word sets.
    Reuses get_word_frequencies() to keep word-extraction logic in one place.
    """
    words_a = set(get_word_frequencies(text_a).keys())
    words_b = set(get_word_frequencies(text_b).keys())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def compute_match(resume_text: str, jd_text: str) -> Dict:
    """
    Core matching algorithm.
    Returns comprehensive match analysis.
    """
    resume_lower = normalize_text(resume_text.lower())
    jd_lower = normalize_text(jd_text.lower())

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

    # Guard: both texts empty → score 0 (not 100 via Jaccard edge case)
    if not resume_lower.strip() and not jd_lower.strip():
        final_score = 0.0
        text_score = 0.0
    else:
        text_score = jaccard_similarity(resume_lower, jd_lower) * 100

        if total_weight > 0:
            final_score = (0.75 * weighted_score) + (0.25 * text_score)
        else:
            final_score = text_score

        final_score = min(100, final_score)

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

    # Dynamic JD keywords (terms not in taxonomy)
    all_taxonomy_kws = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
    dynamic_jd_keywords = extract_dynamic_keywords(jd_text, all_taxonomy_kws)
    dynamic_matched = [
        kw
        for kw in dynamic_jd_keywords
        if re.search(r"\b" + re.escape(kw) + r"\b", resume_lower)
    ]
    dynamic_missing = [kw for kw in dynamic_jd_keywords if kw not in dynamic_matched]

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
        "text_similarity": round(text_score, 1)
        if resume_lower.strip() or jd_lower.strip()
        else 0.0,
        "dynamic_jd_keywords": dynamic_jd_keywords,
        "dynamic_matched": dynamic_matched,
        "dynamic_missing": dynamic_missing,
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
