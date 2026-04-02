"""
Keyword analysis engine.
Extracts, weights, and matches keywords between resume and job description.
"""

import math
import re
from collections import Counter
from datetime import datetime
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


def _clean_jd_markup(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\[\d+(?:\s*,\s*\d+)*\]", "", text)
    return text


def extract_dynamic_keywords(jd_text: str, taxonomy_keywords: Set[str]) -> List[str]:
    """
    Extract potential skill keywords from JD text that are NOT in the
    static taxonomy. Uses requirement contexts, capitalized terms, and
    bullet points as signals.
    """
    jd_text = _clean_jd_markup(jd_text)
    candidates = set()

    # 1. Terms from requirement signal contexts
    for match in REQUIREMENT_SIGNALS.finditer(jd_text):
        phrase = match.group(1).strip()
        for term in re.split(r",\s*|\s+and\s+|\s+or\s+", phrase):
            term = term.strip().lower()
            term = re.sub(r"[^\w\s\+#\./\-]", "", term).strip()
            if (
                len(term) > 2
                and len(term.split()) <= 3
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
            w = re.sub(r"[^\w\s\+#\./\-]", "", w).strip()
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


def bm25_score(
    query_terms: List[str],
    doc_freq: Counter,
    doc_length: int,
    avg_doc_length: float,
    corpus_size: int = 2,
    doc_containing: Dict[str, int] = None,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """
    BM25 relevance score for a document against query terms.
    Uses IDF with smoothing, term frequency saturation, and length normalization.
    """
    if doc_containing is None:
        doc_containing = {}

    score = 0.0
    for term in query_terms:
        tf = doc_freq.get(term, 0)
        n_containing = doc_containing.get(term, 0)

        idf = math.log((corpus_size - n_containing + 0.5) / (n_containing + 0.5) + 1)

        if avg_doc_length > 0:
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * (numerator / denominator)

    return score


def bm25_similarity(text_a: str, text_b: str) -> float:
    """
    Normalized BM25 similarity between two texts (0.0-1.0).
    Uses text_b as query (JD) and text_a as document (resume).
    Normalizes by self-score (document scored against itself).
    """
    freq_a = get_word_frequencies(text_a)
    freq_b = get_word_frequencies(text_b)

    if not freq_a or not freq_b:
        if not freq_a and not freq_b:
            return 1.0
        return 0.0

    words_a = set(freq_a.keys())
    words_b = set(freq_b.keys())
    all_words = words_a | words_b

    len_a = sum(freq_a.values())
    len_b = sum(freq_b.values())
    avg_len = (len_a + len_b) / 2

    doc_containing = {}
    for w in all_words:
        count = 0
        if w in words_a:
            count += 1
        if w in words_b:
            count += 1
        doc_containing[w] = count

    query_terms = list(freq_b.keys())

    actual = bm25_score(
        query_terms,
        freq_a,
        len_a,
        avg_len,
        corpus_size=2,
        doc_containing=doc_containing,
    )

    max_score = bm25_score(
        query_terms,
        freq_b,
        len_b,
        avg_len,
        corpus_size=2,
        doc_containing=doc_containing,
    )

    if max_score <= 0:
        return 0.0

    return min(1.0, actual / max_score)


def extract_ngrams_weighted(text: str, max_n: int = 4) -> Counter:
    """Extract n-grams (n=2 to max_n) with frequency counts."""
    words = [
        w
        for w in re.findall(r"\b[a-z][a-z0-9\+#\.]*\b", text.lower())
        if w not in STOP_WORDS and len(w) > 2
    ]
    ngram_counts = Counter()
    for n in range(2, max_n + 1):
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i : i + n])
            ngram_counts[ngram] += 1
    return ngram_counts


def calculate_keyword_density(text: str, keywords: Set[str]) -> Dict:
    """
    Calculate keyword density metrics. Flags keywords repeated >4 times
    as stuffed (BM25 saturation point).
    """
    words = re.findall(r"\b[a-z][a-z0-9\+#\.]*\b", text.lower())
    total_words = len(words)
    if total_words == 0:
        return {
            "total_words": 0,
            "keyword_mentions": 0,
            "density_pct": 0.0,
            "stuffed_keywords": [],
            "status": "good",
        }

    keyword_mentions = 0
    keyword_counts = Counter()
    for kw in keywords:
        if kw in SPECIAL_PATTERNS:
            pattern = SPECIAL_PATTERNS[kw]
        else:
            pattern = r"\b" + re.escape(kw) + r"\b"
        count = len(re.findall(pattern, text.lower()))
        if count > 0:
            keyword_counts[kw] = count
            keyword_mentions += count

    density = (keyword_mentions / total_words) * 100

    stuffed = [
        {"keyword": kw, "count": count}
        for kw, count in keyword_counts.items()
        if count > 4
    ]

    return {
        "total_words": total_words,
        "keyword_mentions": keyword_mentions,
        "density_pct": round(density, 1),
        "stuffed_keywords": stuffed,
        "status": "good"
        if density <= 8.0
        else ("warning" if density <= 15.0 else "danger"),
    }


# ── YEARS OF EXPERIENCE DETECTION ─────────────────────────────────────────────

YOE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:[-–]?\s*\d+)?\s*"
    r"(?:years?|yrs?)\s*"
    r"(?:of\s+)?(?:experience|exp\.?|professional)?"
    r"(?:\s+(?:with|in|using|of)\s+(.+?))?(?:\.|,|;|\n|$)",
    re.IGNORECASE,
)

DATE_RANGE_PATTERN = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*"
    r"(\d{4}))\s*(?:[-–—]+|to)\s*"
    r"(?:(present|current|now)|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*"
    r"(\d{4}))",
    re.IGNORECASE,
)

YEAR_RANGE_PATTERN = re.compile(
    r"(\d{4})\s*(?:[-–—]+|to)\s*(present|current|now|\d{4})",
    re.IGNORECASE,
)


def extract_yoe_requirements(jd_text: str) -> List[Dict]:
    """Extract years-of-experience requirements from job description."""
    requirements = []
    for match in YOE_PATTERN.finditer(jd_text):
        years = int(match.group(1))
        skill = match.group(2)
        if skill:
            skill = skill.strip().rstrip(".,;")
        requirements.append({"years": years, "skill": skill})
    return requirements


MONTH_TO_NUM = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

MONTH_DATE_RANGE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\.*\s*"
    r"(\d{4})\s*(?:[-–—]+|to)\s*"
    r"(?:(present|current|now)|"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\.*\s*"
    r"(\d{4}))",
    re.IGNORECASE,
)


def estimate_resume_yoe(resume_text: str, current_year: int = None) -> Dict:
    """
    Estimate total years of experience from resume date ranges.
    Merges overlapping ranges to avoid double-counting.
    Uses month-level precision when available, falls back to year-only.
    """
    if current_year is None:
        current_year = datetime.now().year
    current_month = datetime.now().month
    ranges = []

    for match in MONTH_DATE_RANGE.finditer(resume_text):
        start_month_str = match.group(1)[:3].lower()
        start_year = int(match.group(2))
        start_frac = start_year + (MONTH_TO_NUM.get(start_month_str, 1) - 1) / 12

        if match.group(3):
            end_frac = current_year + (current_month - 1) / 12
        else:
            end_month_str = match.group(4)[:3].lower()
            end_year = int(match.group(5))
            end_frac = end_year + MONTH_TO_NUM.get(end_month_str, 12) / 12
        if 1970 <= start_year <= current_year + 1 and start_frac <= end_frac:
            ranges.append((start_frac, end_frac))

    if not ranges:
        for match in YEAR_RANGE_PATTERN.finditer(resume_text):
            start_year = int(match.group(1))
            end_str = match.group(2).lower()
            if end_str in ("present", "current", "now"):
                end_year = current_year
            else:
                end_year = int(end_str)
            if 1970 <= start_year <= current_year + 1 and start_year <= end_year:
                ranges.append((float(start_year), float(end_year)))

    if not ranges:
        return {"total_years": 0, "date_ranges": [], "has_dates": False}

    ranges.sort()
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total_frac = sum(end - start for start, end in merged)
    total = round(total_frac)

    return {
        "total_years": total,
        "date_ranges": [(round(s), round(e)) for s, e in merged],
        "has_dates": True,
    }


# ── SECTION-AWARE SCORING ─────────────────────────────────────────────────────

SECTION_MULTIPLIERS = {
    "skills": 1.5,
    "experience": 1.3,
    "summary": 1.2,
    "projects": 1.1,
    "education": 1.0,
    "other": 1.0,
}

SECTION_HEADERS = {
    "skills": re.compile(
        r"(?:^|\n)\s*(?:skills?|technical\s+skills?|core\s+competencies)\s*\n",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"(?:^|\n)\s*(?:experience|work\s+history|employment|professional\s+experience)\s*\n",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"(?:^|\n)\s*(?:summary|objective|professional\s+summary|profile|about\s+me)\s*\n",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"(?:^|\n)\s*(?:projects?|personal\s+projects?|academic\s+projects?)\s*\n",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"(?:^|\n)\s*(?:education|university|college|degree|certifications?)\s*\n",
        re.IGNORECASE,
    ),
}


def segment_resume(text: str) -> Dict[str, str]:
    """
    Split resume text into section blocks.
    Returns {section_name: section_text}. Text before any header goes into 'other'.
    """
    boundaries = []
    for section_name, pattern in SECTION_HEADERS.items():
        match = pattern.search(text)
        if match:
            boundaries.append((match.start(), section_name))

    if not boundaries:
        return {"other": text}

    boundaries.sort(key=lambda x: x[0])

    sections = {}
    if boundaries[0][0] > 0:
        sections["other"] = text[: boundaries[0][0]]

    for i, (pos, name) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        sections[name] = text[pos:end]

    return sections


def compute_match(
    resume_text: str, jd_text: str, resume_raw: str = "", jd_raw: str = ""
) -> Dict:
    """
    Core matching algorithm.
    Pass resume_raw/jd_raw (original text with newlines) for section detection and YoE.
    Falls back to resume_text/jd_text if raw versions not provided.
    """
    resume_lower = normalize_text(resume_text.lower())
    jd_lower = normalize_text(jd_text.lower())
    resume_original = resume_raw if resume_raw else resume_text
    jd_original = jd_raw if jd_raw else jd_text

    # Extract keywords from both
    jd_keywords = extract_keywords(jd_lower)
    resume_keywords = extract_keywords(resume_lower)

    # Flatten for comparison
    jd_flat = {kw for cats in jd_keywords.values() for kw in cats}
    resume_flat = {kw for cats in resume_keywords.values() for kw in cats}

    # Matched and missing
    matched = jd_flat & resume_flat
    missing = jd_flat - resume_flat

    # Section-aware weighted score (use original text for header detection)
    resume_sections = segment_resume(resume_original.lower())
    total_weight = 0
    matched_weight = 0
    keyword_placement = {}

    for category, data in SKILL_TAXONOMY.items():
        weight = data["weight"]
        jd_cat_kws = set(jd_keywords.get(category, []))

        if jd_cat_kws:
            total_weight += len(jd_cat_kws) * weight

            for kw in jd_cat_kws:
                best_multiplier = 0.0
                best_section = None
                for section_name, section_text in resume_sections.items():
                    if kw in SPECIAL_PATTERNS:
                        pattern = SPECIAL_PATTERNS[kw]
                    else:
                        pattern = r"\b" + re.escape(kw) + r"\b"
                    if re.search(pattern, section_text):
                        mult = SECTION_MULTIPLIERS.get(section_name, 1.0)
                        if mult > best_multiplier:
                            best_multiplier = mult
                            best_section = section_name

                if best_multiplier > 0:
                    matched_weight += weight * min(best_multiplier, 1.5)
                    if best_section:
                        keyword_placement.setdefault(best_section, []).append(kw)

    if total_weight > 0:
        weighted_score = min(100, (matched_weight / total_weight) * 100)
    else:
        weighted_score = 0

    if not resume_lower.strip() and not jd_lower.strip():
        final_score = 0.0
        text_score = 0.0
        dynamic_score = 0.0
    else:
        keyword_score = weighted_score
        text_score = bm25_similarity(resume_lower, jd_lower) * 100

        all_taxonomy_kws = {
            kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]
        }
        dynamic_jd_keywords_early = extract_dynamic_keywords(
            jd_original, all_taxonomy_kws
        )
        dynamic_matched_early = [
            kw
            for kw in dynamic_jd_keywords_early
            if re.search(r"\b" + re.escape(normalize_text(kw)) + r"\b", resume_lower)
        ]

        if dynamic_jd_keywords_early:
            dynamic_score = (
                len(dynamic_matched_early) / len(dynamic_jd_keywords_early)
            ) * 100
        else:
            dynamic_score = 0.0

        # Combined formula: 70% taxonomy + 20% BM25 + 10% dynamic (or 80/20 if no dynamic)
        if total_weight > 0:
            if dynamic_jd_keywords_early:
                final_score = (
                    (0.70 * keyword_score)
                    + (0.20 * text_score)
                    + (0.10 * dynamic_score)
                )
            else:
                final_score = (0.80 * keyword_score) + (0.20 * text_score)
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

    # Extract key phrases from JD not in resume (enhanced: 2-4 grams)
    jd_ngrams = extract_ngrams_weighted(jd_lower, max_n=4)
    resume_ngrams = extract_ngrams_weighted(resume_lower, max_n=4)
    missing_phrases = sorted(
        [
            p
            for p in jd_ngrams
            if p not in resume_ngrams and not any(sw in p.split() for sw in STOP_WORDS)
        ],
        key=lambda x: (len(x.split()), jd_ngrams[x]),
        reverse=True,
    )[:10]

    # Bonus skills in resume not in JD
    bonus_skills = sorted(resume_flat - jd_flat)

    # Dynamic JD keywords (terms not in taxonomy — use original for capitalization detection)
    all_taxonomy_kws = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
    dynamic_jd_keywords = extract_dynamic_keywords(jd_original, all_taxonomy_kws)
    dynamic_matched = [
        kw
        for kw in dynamic_jd_keywords
        if re.search(r"\b" + re.escape(normalize_text(kw)) + r"\b", resume_lower)
    ]
    dynamic_missing = [kw for kw in dynamic_jd_keywords if kw not in dynamic_matched]

    # Grade
    grade = _score_to_grade(final_score)

    # Section analysis
    sections = _analyze_sections(resume_original.lower())

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
        "keyword_placement": keyword_placement,
        "yoe_requirements": extract_yoe_requirements(jd_original),
        "resume_yoe": estimate_resume_yoe(resume_original),
        "keyword_density": calculate_keyword_density(
            resume_lower, resume_flat | matched
        ),
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
