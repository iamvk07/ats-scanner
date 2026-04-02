"""
Unit tests for ATS Scanner.
Run with: python -m pytest tests/ -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ats_scanner.analyzer import (
    extract_keywords,
    compute_match,
    normalize_text,
    bm25_similarity,
    extract_ngrams_weighted,
    segment_resume,
    extract_yoe_requirements,
    estimate_resume_yoe,
    calculate_keyword_density,
    _score_to_grade,
    _analyze_sections,
    get_word_frequencies,
    extract_ngrams,
    jaccard_similarity,
    SKILL_TAXONOMY,
    SYNONYM_MAP,
    STOP_WORDS,
)
from ats_scanner.extractor import clean_text, extract_text


class TestKeywordExtraction(unittest.TestCase):
    def test_extracts_languages(self):
        text = "experience with python and java development"
        result = extract_keywords(text)
        self.assertIn("languages", result)
        self.assertIn("python", result["languages"])
        self.assertIn("java", result["languages"])

    def test_extracts_frameworks(self):
        text = "built with react and flask rest api"
        result = extract_keywords(text)
        self.assertIn("frameworks", result)
        self.assertIn("react", result["frameworks"])
        self.assertIn("flask", result["frameworks"])

    def test_extracts_databases(self):
        text = "postgresql database with redis caching"
        result = extract_keywords(text)
        self.assertIn("databases", result)
        self.assertIn("postgresql", result["databases"])

    def test_extracts_devops(self):
        text = "docker containers github actions ci/cd pipeline"
        result = extract_keywords(text)
        self.assertIn("devops_cloud", result)
        self.assertIn("docker", result["devops_cloud"])

    def test_empty_text(self):
        result = extract_keywords("")
        self.assertEqual(result, {})

    def test_no_false_positives(self):
        text = "hello world this is a test"
        result = extract_keywords(text)
        # Should not find tech keywords in generic text
        langs = result.get("languages", [])
        self.assertNotIn("c", langs)  # 'c' alone should not match

    def test_case_insensitive(self):
        text = "Experience with PYTHON and Java"
        result = extract_keywords(text)
        self.assertIn("python", result.get("languages", []))
        self.assertIn("java", result.get("languages", []))

    def test_c_not_matched_from_cpp(self):
        text = "experienced c++ developer"
        result = extract_keywords(text)
        self.assertIn("c++", result.get("languages", []))
        self.assertNotIn("c", result.get("languages", []))

    def test_c_not_matched_from_csharp(self):
        text = "experienced c# developer"
        result = extract_keywords(text)
        self.assertIn("c#", result.get("languages", []))
        self.assertNotIn("c", result.get("languages", []))

    def test_c_matched_standalone(self):
        text = "experience with c programming"
        result = extract_keywords(text)
        self.assertIn("c", result.get("languages", []))


class TestTaxonomyIntegrity(unittest.TestCase):
    def test_no_cross_category_duplicates(self):
        seen = {}
        for cat, data in SKILL_TAXONOMY.items():
            for kw in data["keywords"]:
                self.assertNotIn(
                    kw,
                    seen,
                    f'"{kw}" is in both "{seen.get(kw)}" and "{cat}"',
                )
                seen[kw] = cat

    def test_taxonomy_keyword_count(self):
        total = sum(len(d["keywords"]) for d in SKILL_TAXONOMY.values())
        self.assertGreaterEqual(total, 197)

    def test_no_alias_duplicates_in_taxonomy(self):
        all_kws = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
        for alias, canonical in SYNONYM_MAP.items():
            self.assertFalse(
                alias in all_kws and canonical in all_kws,
                f'Both alias "{alias}" and canonical "{canonical}" are in taxonomy. '
                f'Remove "{alias}" — it will be handled by SYNONYM_MAP.',
            )


class TestComputeMatch(unittest.TestCase):
    def setUp(self):
        self.strong_resume = clean_text("""
            python java javascript react flask postgresql docker git
            agile scrum ci/cd unit testing oop rest api github actions
            data structures algorithms object oriented programming
        """)
        self.strong_jd = clean_text("""
            looking for python developer with react experience
            postgresql database docker ci/cd github actions agile scrum
            rest api oop data structures
        """)
        self.weak_resume = clean_text("microsoft word excel powerpoint communication")
        self.weak_jd = clean_text("python java react postgresql docker kubernetes aws")

    def test_strong_match_high_score(self):
        result = compute_match(self.strong_resume, self.strong_jd)
        self.assertGreater(result["score"], 60)

    def test_weak_match_low_score(self):
        result = compute_match(self.weak_resume, self.weak_jd)
        self.assertLess(result["score"], 40)

    def test_perfect_match(self):
        text = clean_text("python java react postgresql docker")
        result = compute_match(text, text)
        self.assertGreater(result["score"], 95)

    def test_matched_count(self):
        result = compute_match(self.strong_resume, self.strong_jd)
        self.assertGreater(result["matched_count"], 0)

    def test_missing_count(self):
        result = compute_match(self.weak_resume, self.strong_jd)
        self.assertGreater(result["missing_count"], 0)

    def test_result_keys(self):
        result = compute_match(self.strong_resume, self.strong_jd)
        required_keys = [
            "score",
            "grade",
            "matched_count",
            "missing_count",
            "matched_by_category",
            "missing_by_category",
            "bonus_skills",
            "sections",
        ]
        for key in required_keys:
            self.assertIn(key, result)

    def test_score_range(self):
        result = compute_match(self.strong_resume, self.strong_jd)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_grade_assigned(self):
        result = compute_match(self.strong_resume, self.strong_jd)
        self.assertIn(result["grade"], ["A", "B", "C", "D", "F"])


class TestGrading(unittest.TestCase):
    def test_grade_a(self):
        self.assertEqual(_score_to_grade(90), "A")
        self.assertEqual(_score_to_grade(85), "A")

    def test_grade_b(self):
        self.assertEqual(_score_to_grade(80), "B")
        self.assertEqual(_score_to_grade(75), "B")

    def test_grade_c(self):
        self.assertEqual(_score_to_grade(65), "C")
        self.assertEqual(_score_to_grade(60), "C")

    def test_grade_d(self):
        self.assertEqual(_score_to_grade(50), "D")
        self.assertEqual(_score_to_grade(45), "D")

    def test_grade_f(self):
        self.assertEqual(_score_to_grade(30), "F")
        self.assertEqual(_score_to_grade(0), "F")


class TestTextExtraction(unittest.TestCase):
    def test_clean_text_lowercase(self):
        result = clean_text("Hello WORLD Python")
        self.assertEqual(result, "hello world python")

    def test_clean_text_removes_special(self):
        result = clean_text("hello, world! test@email.com")
        self.assertNotIn(",", result)
        self.assertNotIn("!", result)

    def test_clean_text_preserves_tech(self):
        result = clean_text("C++ and C# are languages")
        self.assertIn("c++", result)
        self.assertIn("c#", result)

    def test_extract_from_string(self):
        result = extract_text("this is raw text input")
        self.assertEqual(result, "this is raw text input")

    def test_extract_txt_file(self):
        # Create temp file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("python developer with react experience")
            tmp_path = f.name
        try:
            result = extract_text(tmp_path)
            self.assertIn("python", result)
        finally:
            os.unlink(tmp_path)

    def test_unsupported_file_type(self):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".odt", delete=False) as f:
            f.write(b"fake")
            tmp = f.name
        try:
            with self.assertRaises(ValueError):
                extract_text(tmp)
        finally:
            os.unlink(tmp)


class TestNgrams(unittest.TestCase):
    def test_bigrams(self):
        text = "python developer with react experience"
        ngrams = extract_ngrams(text, 2)
        self.assertIn("python developer", ngrams)

    def test_empty_text(self):
        ngrams = extract_ngrams("", 2)
        self.assertEqual(ngrams, [])


class TestSectionDetection(unittest.TestCase):
    def test_section_no_false_positive_developer(self):
        text = "python developer\nskills: java, react"
        sections = _analyze_sections(text)
        self.assertFalse(sections["experience"])

    def test_section_detects_header(self):
        text = "some intro\nexperience\njunior dev at company"
        sections = _analyze_sections(text)
        self.assertTrue(sections["experience"])

    def test_section_detects_projects_header(self):
        text = "intro\nprojects\nbuilt a web app"
        sections = _analyze_sections(text)
        self.assertTrue(sections["projects"])


class TestStopWordFiltering(unittest.TestCase):
    def test_ngram_filters_all_stop_words(self):
        resume = clean_text("python")
        jd = clean_text("the python experience with good skills")
        result = compute_match(resume, jd)
        for phrase in result["missing_phrases"]:
            words = phrase.split()
            has_stop = any(w in STOP_WORDS for w in words)
            self.assertFalse(
                has_stop,
                f'Phrase "{phrase}" contains a stop word and should be filtered',
            )


class TestWordFrequency(unittest.TestCase):
    def test_counts_words(self):
        text = "python python java python java"
        freq = get_word_frequencies(text)
        self.assertEqual(freq["python"], 3)
        self.assertEqual(freq["java"], 2)

    def test_excludes_stop_words(self):
        text = "the quick brown fox"
        freq = get_word_frequencies(text)
        self.assertNotIn("the", freq)


class TestTexExtraction(unittest.TestCase):
    def test_extract_tex_file(self):
        import tempfile

        content = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
\section{Skills}
Python, Java, React, PostgreSQL
\textbf{Docker} and \emph{Kubernetes}
\end{document}"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = f.name
        try:
            result = extract_text(tmp)
            self.assertIn("Python", result)
            self.assertIn("Docker", result)
            self.assertIn("Kubernetes", result)
            self.assertNotIn("\\documentclass", result)
            self.assertNotIn("\\begin", result)
            self.assertNotIn("\\usepackage", result)
        finally:
            os.unlink(tmp)

    def test_strip_latex_preserves_content(self):
        from ats_scanner.extractor import strip_latex

        text = r"\textbf{Python} and \emph{Java} developer"
        result = strip_latex(text)
        self.assertIn("Python", result)
        self.assertIn("Java", result)
        self.assertIn("developer", result)
        self.assertNotIn("\\textbf", result)
        self.assertNotIn("\\emph", result)

    def test_strip_latex_removes_comments(self):
        from ats_scanner.extractor import strip_latex

        text = "Python developer % this is a comment\nJava expert"
        result = strip_latex(text)
        self.assertIn("Python", result)
        self.assertIn("Java", result)
        self.assertNotIn("comment", result)

    def test_strip_latex_handles_href(self):
        from ats_scanner.extractor import strip_latex

        text = r"\href{https://github.com/user}{My GitHub Profile}"
        result = strip_latex(text)
        self.assertIn("My GitHub Profile", result)
        self.assertNotIn("https://", result)

    def test_strip_latex_handles_sections(self):
        from ats_scanner.extractor import strip_latex

        text = r"\section{Experience}\subsection{Company A}"
        result = strip_latex(text)
        self.assertIn("Experience", result)
        self.assertIn("Company A", result)

    def test_strip_latex_removes_preamble(self):
        from ats_scanner.extractor import strip_latex

        text = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
Actual content here"""
        result = strip_latex(text)
        self.assertIn("Actual content", result)
        self.assertNotIn("documentclass", result)
        self.assertNotIn("geometry", result)

    def test_strip_latex_escaped_chars(self):
        from ats_scanner.extractor import strip_latex

        text = r"R\&D department, 100\% effort"
        result = strip_latex(text)
        self.assertIn("R", result)
        self.assertIn("D department", result)

    def test_strip_latex_nested_commands(self):
        from ats_scanner.extractor import strip_latex

        text = r"\textbf{\emph{Python}} and \textit{\texttt{Java}} developer"
        result = strip_latex(text)
        self.assertIn("Python", result)
        self.assertIn("Java", result)
        self.assertIn("developer", result)
        self.assertNotIn("\\textbf", result)
        self.assertNotIn("\\emph", result)
        self.assertNotIn("{", result)


class TestDocxExtraction(unittest.TestCase):
    def _make_docx(self, text_content):
        import tempfile
        import zipfile
        from xml.etree.ElementTree import Element, SubElement, tostring

        ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        doc = Element(f"{{{ns}}}document")
        body = SubElement(doc, f"{{{ns}}}body")
        para = SubElement(body, f"{{{ns}}}p")
        run = SubElement(para, f"{{{ns}}}r")
        text = SubElement(run, f"{{{ns}}}t")
        text.text = text_content

        xml_bytes = tostring(doc, encoding="unicode").encode("utf-8")

        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        with zipfile.ZipFile(tmp, "w") as z:
            z.writestr("word/document.xml", xml_bytes)
        tmp.close()
        return tmp.name

    def test_extract_docx_basic(self):
        path = self._make_docx("Python developer with React and PostgreSQL")
        try:
            result = extract_text(path)
            self.assertIn("Python", result)
            self.assertIn("React", result)
            self.assertIn("PostgreSQL", result)
        finally:
            os.unlink(path)

    def test_extract_docx_keywords_match(self):
        from ats_scanner.analyzer import extract_keywords

        path = self._make_docx("Experience with Python, Java, Docker, and PostgreSQL")
        try:
            text = extract_text(path)
            kws = extract_keywords(text.lower())
            self.assertIn("python", kws.get("languages", []))
            self.assertIn("java", kws.get("languages", []))
        finally:
            os.unlink(path)

    def test_invalid_docx_raises(self):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"this is not a zip file at all")
            tmp = f.name
        try:
            with self.assertRaises(ValueError):
                extract_text(tmp)
        finally:
            os.unlink(tmp)

    def test_empty_docx_raises(self):
        import tempfile
        import zipfile

        ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        xml = f'<w:document xmlns:w="{ns}"><w:body></w:body></w:document>'
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        with zipfile.ZipFile(tmp, "w") as z:
            z.writestr("word/document.xml", xml)
        tmp.close()
        try:
            with self.assertRaises(ValueError):
                extract_text(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_docx_missing_document_xml(self):
        import tempfile
        import zipfile

        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        with zipfile.ZipFile(tmp, "w") as z:
            z.writestr("other/file.xml", "<root/>")
        tmp.close()
        try:
            with self.assertRaises(ValueError):
                extract_text(tmp.name)
        finally:
            os.unlink(tmp.name)


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical_text(self):
        text = "python developer with react and docker experience"
        self.assertAlmostEqual(jaccard_similarity(text, text), 1.0)

    def test_no_overlap(self):
        self.assertAlmostEqual(
            jaccard_similarity("python java react", "marketing sales finance"), 0.0
        )

    def test_partial_overlap(self):
        score = jaccard_similarity(
            "python java react docker", "python react angular vue"
        )
        self.assertGreater(score, 0.2)
        self.assertLess(score, 0.8)

    def test_empty_both(self):
        self.assertAlmostEqual(jaccard_similarity("", ""), 1.0)

    def test_empty_one(self):
        self.assertAlmostEqual(jaccard_similarity("python", ""), 0.0)

    def test_stop_words_ignored(self):
        score = jaccard_similarity("the python developer", "a python engineer")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)


class TestIdenticalTextScoring(unittest.TestCase):
    def test_identical_tech_text_scores_high(self):
        text = clean_text("python java react postgresql docker aws kubernetes")
        result = compute_match(text, text)
        self.assertGreater(result["score"], 95)

    def test_identical_non_tech_text_scores_high(self):
        text = clean_text(
            "Marketing manager with 10 years of brand strategy experience "
            "leading cross-functional campaigns and driving revenue growth"
        )
        result = compute_match(text, text)
        self.assertGreater(result["score"], 95)

    def test_identical_mixed_text_scores_high(self):
        text = clean_text(
            "Software developer with python and react experience "
            "built web applications for enterprise clients"
        )
        result = compute_match(text, text)
        self.assertGreater(result["score"], 95)

    def test_no_overlap_scores_low(self):
        resume = clean_text("python java react docker kubernetes aws")
        jd = clean_text("marketing sales finance accounting budgeting")
        result = compute_match(resume, jd)
        self.assertLess(result["score"], 15)

    def test_empty_resume_scores_zero(self):
        result = compute_match("", "python developer")
        self.assertEqual(result["score"], 0)

    def test_both_empty_scores_zero(self):
        result = compute_match("", "")
        self.assertEqual(result["score"], 0)


class TestSectionAwareScoring(unittest.TestCase):
    def test_keyword_in_skills_scores_higher(self):
        resume_skills = "skills\npython java\nexperience\nworked at company"
        resume_other = "some intro text\npython java"
        jd = "requires python java react docker postgresql kubernetes aws"
        result_skills = compute_match(resume_skills, jd)
        result_other = compute_match(resume_other, jd)
        self.assertGreaterEqual(result_skills["score"], result_other["score"])

    def test_segment_resume_basic(self):
        text = "John Doe\nskills\npython java\nexperience\nworked at company"
        sections = segment_resume(text)
        self.assertIn("skills", sections)
        self.assertIn("experience", sections)

    def test_segment_resume_no_headers(self):
        text = "just some plain text without any section headers"
        sections = segment_resume(text)
        self.assertIn("other", sections)
        self.assertEqual(len(sections), 1)

    def test_keyword_placement_in_result(self):
        resume = clean_text("skills\npython java\nexperience\nworked with react")
        jd = clean_text("requires python java react")
        result = compute_match(resume, jd)
        self.assertIn("keyword_placement", result)


class TestBM25(unittest.TestCase):
    def test_identical_text_scores_high(self):
        score = bm25_similarity(
            "python developer react docker", "python developer react docker"
        )
        self.assertGreater(score, 0.95)

    def test_no_overlap_scores_zero(self):
        score = bm25_similarity("python java react", "marketing sales finance")
        self.assertAlmostEqual(score, 0.0)

    def test_partial_overlap(self):
        score = bm25_similarity(
            "python java react docker aws", "python react angular vue"
        )
        self.assertGreater(score, 0.1)
        self.assertLess(score, 0.9)

    def test_keyword_repetition_saturates(self):
        score_1x = bm25_similarity("python developer", "python developer")
        score_5x = bm25_similarity(
            "python python python python python developer",
            "python developer",
        )
        self.assertLess(score_5x / max(score_1x, 0.001), 2.0)

    def test_empty_texts(self):
        self.assertAlmostEqual(bm25_similarity("", ""), 1.0)
        self.assertAlmostEqual(bm25_similarity("python", ""), 0.0)
        self.assertAlmostEqual(bm25_similarity("", "python"), 0.0)


class TestEnhancedNgrams(unittest.TestCase):
    def test_trigrams_extracted(self):
        text = "machine learning engineer with deep learning experience"
        ngrams = extract_ngrams_weighted(text, max_n=3)
        self.assertIn("machine learning engineer", ngrams)

    def test_4grams_extracted(self):
        text = "continuous integration continuous deployment pipeline setup"
        ngrams = extract_ngrams_weighted(text, max_n=4)
        four_grams = [k for k in ngrams if len(k.split()) == 4]
        self.assertGreater(len(four_grams), 0)


class TestDynamicKeywordExtraction(unittest.TestCase):
    def test_extracts_from_requirement_context(self):
        jd = "Experience with Terraform and Pulumi required"
        from ats_scanner.analyzer import extract_dynamic_keywords

        taxonomy = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
        dynamic = extract_dynamic_keywords(jd, taxonomy)
        self.assertIn("pulumi", dynamic)

    def test_does_not_duplicate_taxonomy(self):
        jd = "Experience with Python and Docker"
        from ats_scanner.analyzer import extract_dynamic_keywords

        taxonomy = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
        dynamic = extract_dynamic_keywords(jd, taxonomy)
        self.assertNotIn("python", dynamic)
        self.assertNotIn("docker", dynamic)

    def test_extracts_from_bullets(self):
        jd = "Requirements:\n- Datadog monitoring\n- Grafana dashboards"
        from ats_scanner.analyzer import extract_dynamic_keywords

        taxonomy = {kw for cat in SKILL_TAXONOMY.values() for kw in cat["keywords"]}
        dynamic = extract_dynamic_keywords(jd, taxonomy)
        has_datadog = any("datadog" in d for d in dynamic)
        has_grafana = any("grafana" in d for d in dynamic)
        self.assertTrue(
            has_datadog or has_grafana,
            f"Expected datadog or grafana in dynamic keywords, got: {dynamic}",
        )

    def test_dynamic_keywords_in_result(self):
        resume = clean_text("python developer with react experience")
        jd = clean_text("python react and pulumi experience required")
        result = compute_match(resume, jd)
        self.assertIn("dynamic_jd_keywords", result)
        self.assertIn("dynamic_matched", result)
        self.assertIn("dynamic_missing", result)


class TestKeywordDensity(unittest.TestCase):
    def test_normal_density(self):
        words = " ".join([f"word{i}" for i in range(100)])
        text = f"python {words}"
        keywords = {"python"}
        result = calculate_keyword_density(text, keywords)
        self.assertLess(result["density_pct"], 3.0)
        self.assertEqual(result["status"], "good")

    def test_stuffed_keyword_detected(self):
        text = "python python python python python python developer"
        keywords = {"python"}
        result = calculate_keyword_density(text, keywords)
        self.assertEqual(len(result["stuffed_keywords"]), 1)
        self.assertEqual(result["stuffed_keywords"][0]["keyword"], "python")

    def test_empty_text(self):
        result = calculate_keyword_density("", {"python"})
        self.assertEqual(result["density_pct"], 0.0)

    def test_density_in_result(self):
        resume = clean_text("python developer with react experience")
        jd = clean_text("python react developer")
        result = compute_match(resume, jd)
        self.assertIn("keyword_density", result)


class TestYoEDetection(unittest.TestCase):
    def test_extract_yoe_simple(self):
        jd = "Requires 5+ years of Python experience"
        reqs = extract_yoe_requirements(jd)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["years"], 5)

    def test_extract_yoe_with_skill(self):
        jd = "3 years experience with React"
        reqs = extract_yoe_requirements(jd)
        self.assertEqual(reqs[0]["years"], 3)
        self.assertIn("react", reqs[0]["skill"].lower())

    def test_estimate_resume_yoe(self):
        resume = (
            "Software Developer\nJan 2020 - Present\nJunior Dev\nJun 2018 - Dec 2019"
        )
        yoe = estimate_resume_yoe(resume, current_year=2026)
        self.assertTrue(yoe["has_dates"])
        self.assertGreaterEqual(yoe["total_years"], 7)

    def test_overlapping_ranges_merged(self):
        resume = "Role A: 2018 - 2022\nRole B: 2020 - 2024"
        yoe = estimate_resume_yoe(resume, current_year=2026)
        self.assertEqual(yoe["total_years"], 6)

    def test_no_dates_returns_zero(self):
        resume = "Python developer with extensive experience"
        yoe = estimate_resume_yoe(resume)
        self.assertFalse(yoe["has_dates"])
        self.assertEqual(yoe["total_years"], 0)

    def test_yoe_in_result(self):
        resume = "python developer\nJan 2020 - Present"
        jd = "5+ years of python experience"
        result = compute_match(resume, jd)
        self.assertIn("yoe_requirements", result)
        self.assertIn("resume_yoe", result)


class TestSynonymExpansion(unittest.TestCase):
    def test_postgres_matches_postgresql(self):
        resume = clean_text("experience with postgres databases")
        jd = clean_text("requires postgresql experience")
        result = compute_match(resume, jd)
        self.assertIn("postgresql", result["matched_by_category"].get("databases", []))
        self.assertEqual(result["missing_count"], 0)

    def test_js_matches_javascript(self):
        resume = clean_text("proficient in js and react")
        jd = clean_text("javascript and react developer")
        result = compute_match(resume, jd)
        self.assertIn("javascript", result["matched_by_category"].get("languages", []))

    def test_k8s_matches_kubernetes(self):
        resume = clean_text("deployed on k8s clusters")
        jd = clean_text("kubernetes orchestration required")
        result = compute_match(resume, jd)
        self.assertIn(
            "kubernetes", result["matched_by_category"].get("devops_cloud", [])
        )

    def test_bidirectional_synonym(self):
        resume = clean_text("experience with postgresql")
        jd = clean_text("requires postgres experience")
        result = compute_match(resume, jd)
        self.assertIn("postgresql", result["matched_by_category"].get("databases", []))

    def test_normalize_preserves_non_synonyms(self):
        text = "python developer with docker experience"
        result = normalize_text(text)
        self.assertIn("python", result)
        self.assertIn("docker", result)

    def test_multi_word_synonym(self):
        result = normalize_text("deployed on amazon web services")
        self.assertIn("aws", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
