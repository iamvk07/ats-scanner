import { describe, it, expect } from "vitest";
import {
  extractKeywords,
  computeMatch,
  normalizeText,
  bm25Similarity,
  extractNgramsWeighted,
  segmentResume,
  extractYoeRequirements,
  estimateResumeYoe,
  calculateKeywordDensity,
  scoreToGrade,
  analyzeSections,
  getWordFrequencies,
  extractNgrams,
  jaccardSimilarity,
  extractDynamicKeywords,
  cleanText,
  SKILL_TAXONOMY,
  SYNONYM_MAP,
  STOP_WORDS,
} from "../src/index.js";

describe("KeywordExtraction", () => {
  it("extracts languages", () => {
    const result = extractKeywords("experience with python and java development");
    expect(result.languages).toBeDefined();
    expect(result.languages).toContain("python");
    expect(result.languages).toContain("java");
  });

  it("extracts frameworks", () => {
    const result = extractKeywords("built with react and flask rest api");
    expect(result.frameworks).toBeDefined();
    expect(result.frameworks).toContain("react");
    expect(result.frameworks).toContain("flask");
  });

  it("extracts databases", () => {
    const result = extractKeywords("postgresql database with redis caching");
    expect(result.databases).toBeDefined();
    expect(result.databases).toContain("postgresql");
  });

  it("extracts devops", () => {
    const result = extractKeywords("docker containers github actions ci/cd pipeline");
    expect(result.devops_cloud).toBeDefined();
    expect(result.devops_cloud).toContain("docker");
  });

  it("returns empty for empty text", () => {
    expect(extractKeywords("")).toEqual({});
  });

  it("avoids false positives", () => {
    const result = extractKeywords("hello world this is a test");
    const langs = result.languages ?? [];
    expect(langs).not.toContain("c");
  });

  it("is case insensitive", () => {
    const result = extractKeywords("Experience with PYTHON and Java");
    expect(result.languages).toContain("python");
    expect(result.languages).toContain("java");
  });

  it("does not match c from c++", () => {
    const result = extractKeywords("experienced c++ developer");
    expect(result.languages).toContain("c++");
    expect(result.languages).not.toContain("c");
  });

  it("does not match c from c#", () => {
    const result = extractKeywords("experienced c# developer");
    expect(result.languages).toContain("c#");
    expect(result.languages).not.toContain("c");
  });

  it("matches standalone c", () => {
    const result = extractKeywords("experience with c programming");
    expect(result.languages).toContain("c");
  });
});

describe("TaxonomyIntegrity", () => {
  it("has no cross-category duplicates", () => {
    const seen: Record<string, string> = {};
    for (const [cat, data] of Object.entries(SKILL_TAXONOMY)) {
      for (const kw of data.keywords) {
        expect(seen[kw]).toBeUndefined();
        seen[kw] = cat;
      }
    }
  });

  it("has at least 197 keywords", () => {
    const total = Object.values(SKILL_TAXONOMY).reduce(
      (sum, d) => sum + d.keywords.length,
      0,
    );
    expect(total).toBeGreaterThanOrEqual(197);
  });

  it("has no alias duplicates in taxonomy", () => {
    const allKws = new Set(
      Object.values(SKILL_TAXONOMY).flatMap((cat) => [...cat.keywords]),
    );
    for (const [alias, canonical] of Object.entries(SYNONYM_MAP)) {
      const bothPresent = allKws.has(alias) && allKws.has(canonical);
      expect(bothPresent).toBe(false);
    }
  });
});

describe("ComputeMatch", () => {
  const strongResume = cleanText(
    "python java javascript react flask postgresql docker git " +
      "agile scrum ci/cd unit testing oop rest api github actions " +
      "data structures algorithms object oriented programming",
  );
  const strongJd = cleanText(
    "looking for python developer with react experience " +
      "postgresql database docker ci/cd github actions agile scrum " +
      "rest api oop data structures",
  );
  const weakResume = cleanText("microsoft word excel powerpoint communication");
  const weakJd = cleanText(
    "python java react postgresql docker kubernetes aws",
  );

  it("strong match gives high score", () => {
    const result = computeMatch(strongResume, strongJd);
    expect(result.score).toBeGreaterThan(60);
  });

  it("weak match gives low score", () => {
    const result = computeMatch(weakResume, weakJd);
    expect(result.score).toBeLessThan(40);
  });

  it("perfect match scores above 95", () => {
    const text = cleanText("python java react postgresql docker");
    const result = computeMatch(text, text);
    expect(result.score).toBeGreaterThan(95);
  });

  it("has matched count", () => {
    const result = computeMatch(strongResume, strongJd);
    expect(result.matched_count).toBeGreaterThan(0);
  });

  it("has missing count", () => {
    const result = computeMatch(weakResume, strongJd);
    expect(result.missing_count).toBeGreaterThan(0);
  });

  it("returns all required keys", () => {
    const result = computeMatch(strongResume, strongJd);
    const keys = [
      "score", "grade", "matched_count", "missing_count",
      "matched_by_category", "missing_by_category", "bonus_skills", "sections",
    ] as const;
    for (const key of keys) {
      expect(result).toHaveProperty(key);
    }
  });

  it("score is in range 0-100", () => {
    const result = computeMatch(strongResume, strongJd);
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(100);
  });

  it("grade is valid", () => {
    const result = computeMatch(strongResume, strongJd);
    expect(["A", "B", "C", "D", "F"]).toContain(result.grade);
  });
});

describe("Grading", () => {
  it("grade A", () => {
    expect(scoreToGrade(90)).toBe("A");
    expect(scoreToGrade(85)).toBe("A");
  });
  it("grade B", () => {
    expect(scoreToGrade(80)).toBe("B");
    expect(scoreToGrade(75)).toBe("B");
  });
  it("grade C", () => {
    expect(scoreToGrade(65)).toBe("C");
    expect(scoreToGrade(60)).toBe("C");
  });
  it("grade D", () => {
    expect(scoreToGrade(50)).toBe("D");
    expect(scoreToGrade(45)).toBe("D");
  });
  it("grade F", () => {
    expect(scoreToGrade(30)).toBe("F");
    expect(scoreToGrade(0)).toBe("F");
  });
});

describe("IdenticalTextScoring", () => {
  it("identical tech text scores high", () => {
    const text = cleanText("python java react postgresql docker aws kubernetes");
    const result = computeMatch(text, text);
    expect(result.score).toBeGreaterThan(95);
  });

  it("identical non-tech text scores high", () => {
    const text = cleanText(
      "Marketing manager with 10 years of brand strategy experience " +
        "leading cross-functional campaigns and driving revenue growth",
    );
    const result = computeMatch(text, text);
    expect(result.score).toBeGreaterThan(95);
  });

  it("identical mixed text scores high", () => {
    const text = cleanText(
      "Software developer with python and react experience " +
        "built web applications for enterprise clients",
    );
    const result = computeMatch(text, text);
    expect(result.score).toBeGreaterThan(95);
  });

  it("no overlap scores low", () => {
    const resume = cleanText("python java react docker kubernetes aws");
    const jd = cleanText("marketing sales finance accounting budgeting");
    const result = computeMatch(resume, jd);
    expect(result.score).toBeLessThan(15);
  });

  it("empty resume scores zero", () => {
    const result = computeMatch("", "python developer");
    expect(result.score).toBe(0);
  });

  it("both empty scores zero", () => {
    const result = computeMatch("", "");
    expect(result.score).toBe(0);
  });
});

describe("SectionAwareScoring", () => {
  it("keyword in skills scores higher or equal", () => {
    const resumeSkills = "skills\npython java\nexperience\nworked at company";
    const resumeOther = "some intro text\npython java";
    const jd = "requires python java react docker postgresql kubernetes aws";
    const resultSkills = computeMatch(resumeSkills, jd);
    const resultOther = computeMatch(resumeOther, jd);
    expect(resultSkills.score).toBeGreaterThanOrEqual(resultOther.score);
  });

  it("segments resume basic", () => {
    const text = "John Doe\nskills\npython java\nexperience\nworked at company";
    const sections = segmentResume(text);
    expect(sections).toHaveProperty("skills");
    expect(sections).toHaveProperty("experience");
  });

  it("segments resume with no headers", () => {
    const text = "just some plain text without any section headers";
    const sections = segmentResume(text);
    expect(sections).toHaveProperty("other");
    expect(Object.keys(sections)).toHaveLength(1);
  });

  it("keyword placement in result", () => {
    const resume = cleanText("skills\npython java\nexperience\nworked with react");
    const jd = cleanText("requires python java react");
    const result = computeMatch(resume, jd);
    expect(result).toHaveProperty("keyword_placement");
  });
});

describe("BM25", () => {
  it("identical text scores high", () => {
    const score = bm25Similarity(
      "python developer react docker",
      "python developer react docker",
    );
    expect(score).toBeGreaterThan(0.95);
  });

  it("no overlap scores zero", () => {
    const score = bm25Similarity(
      "python java react",
      "marketing sales finance",
    );
    expect(score).toBeCloseTo(0.0);
  });

  it("partial overlap", () => {
    const score = bm25Similarity(
      "python java react docker aws",
      "python react angular vue",
    );
    expect(score).toBeGreaterThan(0.1);
    expect(score).toBeLessThan(0.9);
  });

  it("keyword repetition saturates", () => {
    const score1x = bm25Similarity("python developer", "python developer");
    const score5x = bm25Similarity(
      "python python python python python developer",
      "python developer",
    );
    expect(score5x / Math.max(score1x, 0.001)).toBeLessThan(2.0);
  });

  it("empty texts", () => {
    expect(bm25Similarity("", "")).toBeCloseTo(1.0);
    expect(bm25Similarity("python", "")).toBeCloseTo(0.0);
    expect(bm25Similarity("", "python")).toBeCloseTo(0.0);
  });
});

describe("EnhancedNgrams", () => {
  it("extracts trigrams", () => {
    const text = "machine learning engineer with deep learning experience";
    const ngrams = extractNgramsWeighted(text, 3);
    expect(ngrams.has("machine learning engineer")).toBe(true);
  });

  it("extracts 4-grams", () => {
    const text = "continuous integration continuous deployment pipeline setup";
    const ngrams = extractNgramsWeighted(text, 4);
    const fourGrams = [...ngrams.keys()].filter(
      (k) => k.split(" ").length === 4,
    );
    expect(fourGrams.length).toBeGreaterThan(0);
  });
});

describe("DynamicKeywordExtraction", () => {
  const taxonomy = new Set(
    Object.values(SKILL_TAXONOMY).flatMap((cat) => [...cat.keywords]),
  );

  it("extracts from requirement context", () => {
    const jd = "Experience with Terraform and Pulumi required";
    const dynamic = extractDynamicKeywords(jd, taxonomy);
    expect(dynamic).toContain("pulumi");
  });

  it("does not duplicate taxonomy", () => {
    const jd = "Experience with Python and Docker";
    const dynamic = extractDynamicKeywords(jd, taxonomy);
    expect(dynamic).not.toContain("python");
    expect(dynamic).not.toContain("docker");
  });

  it("extracts from bullets", () => {
    const jd = "Requirements:\n- Datadog monitoring\n- Grafana dashboards";
    const dynamic = extractDynamicKeywords(jd, taxonomy);
    const hasDatadog = dynamic.some((d) => d.includes("datadog"));
    const hasGrafana = dynamic.some((d) => d.includes("grafana"));
    expect(hasDatadog || hasGrafana).toBe(true);
  });

  it("dynamic keywords in result", () => {
    const resume = cleanText("python developer with react experience");
    const jd = cleanText("python react and pulumi experience required");
    const result = computeMatch(resume, jd);
    expect(result).toHaveProperty("dynamic_jd_keywords");
    expect(result).toHaveProperty("dynamic_matched");
    expect(result).toHaveProperty("dynamic_missing");
  });
});

describe("KeywordDensity", () => {
  it("normal density", () => {
    const words = Array.from({ length: 100 }, (_, i) => `word${i}`).join(" ");
    const text = `python ${words}`;
    const result = calculateKeywordDensity(text, new Set(["python"]));
    expect(result.density_pct).toBeLessThan(3.0);
    expect(result.status).toBe("good");
  });

  it("detects stuffed keyword", () => {
    const text = "python python python python python python developer";
    const result = calculateKeywordDensity(text, new Set(["python"]));
    expect(result.stuffed_keywords).toHaveLength(1);
    expect(result.stuffed_keywords[0].keyword).toBe("python");
  });

  it("empty text", () => {
    const result = calculateKeywordDensity("", new Set(["python"]));
    expect(result.density_pct).toBe(0);
  });

  it("density in result", () => {
    const resume = cleanText("python developer with react experience");
    const jd = cleanText("python react developer");
    const result = computeMatch(resume, jd);
    expect(result).toHaveProperty("keyword_density");
  });
});

describe("YoEDetection", () => {
  it("extracts simple yoe", () => {
    const jd = "Requires 5+ years of Python experience";
    const reqs = extractYoeRequirements(jd);
    expect(reqs).toHaveLength(1);
    expect(reqs[0].years).toBe(5);
  });

  it("extracts yoe with skill", () => {
    const jd = "3 years experience with React";
    const reqs = extractYoeRequirements(jd);
    expect(reqs[0].years).toBe(3);
    expect(reqs[0].skill?.toLowerCase()).toContain("react");
  });

  it("estimates resume yoe", () => {
    const resume =
      "Software Developer\nJan 2020 - Present\nJunior Dev\nJun 2018 - Dec 2019";
    const yoe = estimateResumeYoe(resume, 2026);
    expect(yoe.has_dates).toBe(true);
    expect(yoe.total_years).toBeGreaterThanOrEqual(7);
  });

  it("merges overlapping ranges", () => {
    const resume = "Role A: 2018 - 2022\nRole B: 2020 - 2024";
    const yoe = estimateResumeYoe(resume, 2026);
    expect(yoe.total_years).toBe(6);
  });

  it("returns zero for no dates", () => {
    const resume = "Python developer with extensive experience";
    const yoe = estimateResumeYoe(resume);
    expect(yoe.has_dates).toBe(false);
    expect(yoe.total_years).toBe(0);
  });

  it("yoe in result", () => {
    const resume = "python developer\nJan 2020 - Present";
    const jd = "5+ years of python experience";
    const result = computeMatch(resume, jd);
    expect(result).toHaveProperty("yoe_requirements");
    expect(result).toHaveProperty("resume_yoe");
  });
});

describe("SynonymExpansion", () => {
  it("postgres matches postgresql", () => {
    const resume = cleanText("experience with postgres databases");
    const jd = cleanText("requires postgresql experience");
    const result = computeMatch(resume, jd);
    expect(result.matched_by_category.databases ?? []).toContain("postgresql");
    expect(result.missing_count).toBe(0);
  });

  it("js matches javascript", () => {
    const resume = cleanText("proficient in js and react");
    const jd = cleanText("javascript and react developer");
    const result = computeMatch(resume, jd);
    expect(result.matched_by_category.languages ?? []).toContain("javascript");
  });

  it("k8s matches kubernetes", () => {
    const resume = cleanText("deployed on k8s clusters");
    const jd = cleanText("kubernetes orchestration required");
    const result = computeMatch(resume, jd);
    expect(result.matched_by_category.devops_cloud ?? []).toContain("kubernetes");
  });

  it("bidirectional synonym", () => {
    const resume = cleanText("experience with postgresql");
    const jd = cleanText("requires postgres experience");
    const result = computeMatch(resume, jd);
    expect(result.matched_by_category.databases ?? []).toContain("postgresql");
  });

  it("preserves non-synonyms", () => {
    const text = "python developer with docker experience";
    const result = normalizeText(text);
    expect(result).toContain("python");
    expect(result).toContain("docker");
  });

  it("multi-word synonym", () => {
    const result = normalizeText("deployed on amazon web services");
    expect(result).toContain("aws");
  });
});

describe("Ngrams", () => {
  it("extracts bigrams", () => {
    const text = "python developer with react experience";
    const ngrams = extractNgrams(text, 2);
    expect(ngrams).toContain("python developer");
  });

  it("returns empty for empty text", () => {
    expect(extractNgrams("", 2)).toEqual([]);
  });
});

describe("SectionDetection", () => {
  it("no false positive for developer", () => {
    const text = "python developer\nskills: java, react";
    const sections = analyzeSections(text);
    expect(sections.experience).toBe(false);
  });

  it("detects experience header", () => {
    const text = "some intro\nexperience\njunior dev at company";
    const sections = analyzeSections(text);
    expect(sections.experience).toBe(true);
  });

  it("detects projects header", () => {
    const text = "intro\nprojects\nbuilt a web app";
    const sections = analyzeSections(text);
    expect(sections.projects).toBe(true);
  });
});

describe("StopWordFiltering", () => {
  it("ngrams filter all stop words", () => {
    const resume = cleanText("python");
    const jd = cleanText("the python experience with good skills");
    const result = computeMatch(resume, jd);
    for (const phrase of result.missing_phrases) {
      const hasStop = phrase.split(" ").some((w) => STOP_WORDS.has(w));
      expect(hasStop).toBe(false);
    }
  });
});

describe("WordFrequency", () => {
  it("counts words", () => {
    const text = "python python java python java";
    const freq = getWordFrequencies(text);
    expect(freq.get("python")).toBe(3);
    expect(freq.get("java")).toBe(2);
  });

  it("excludes stop words", () => {
    const text = "the quick brown fox";
    const freq = getWordFrequencies(text);
    expect(freq.has("the")).toBe(false);
  });
});

describe("JaccardSimilarity", () => {
  it("identical text", () => {
    const text = "python developer with react and docker experience";
    expect(jaccardSimilarity(text, text)).toBeCloseTo(1.0);
  });

  it("no overlap", () => {
    expect(
      jaccardSimilarity("python java react", "marketing sales finance"),
    ).toBeCloseTo(0.0);
  });

  it("partial overlap", () => {
    const score = jaccardSimilarity(
      "python java react docker",
      "python react angular vue",
    );
    expect(score).toBeGreaterThan(0.2);
    expect(score).toBeLessThan(0.8);
  });

  it("empty both", () => {
    expect(jaccardSimilarity("", "")).toBeCloseTo(1.0);
  });

  it("empty one", () => {
    expect(jaccardSimilarity("python", "")).toBeCloseTo(0.0);
  });

  it("stop words ignored", () => {
    const score = jaccardSimilarity(
      "the python developer",
      "a python engineer",
    );
    expect(score).toBeGreaterThan(0.0);
    expect(score).toBeLessThan(1.0);
  });
});
