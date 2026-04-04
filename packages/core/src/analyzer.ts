import type {
  KeywordsByCategory,
  KeywordPlacement,
  KeywordDensityResult,
  YoeRequirement,
  ResumeYoe,
  SectionAnalysis,
  MatchResult,
} from "./types.js";

import {
  SKILL_TAXONOMY,
  SYNONYM_MAP,
  SORTED_SYNONYMS,
  STOP_WORDS,
  SPECIAL_PATTERNS,
  SECTION_MULTIPLIERS,
  SECTION_HEADERS,
} from "./taxonomy.js";

export function normalizeText(text: string): string {
  let result = text;
  for (const [alias, canonical] of SORTED_SYNONYMS) {
    const escaped = alias.replace(/[+.]/g, "\\$&").replace(/\//g, "\\/");
    const pat = new RegExp("\\b" + escaped + "\\b", "gi");
    result = result.replace(pat, canonical);
  }
  return result;
}

export function extractKeywords(text: string): KeywordsByCategory {
  const low = text.toLowerCase();
  const found: KeywordsByCategory = {};

  for (const [cat, data] of Object.entries(SKILL_TAXONOMY)) {
    const matches: string[] = [];
    for (const kw of data.keywords) {
      const pat =
        SPECIAL_PATTERNS[kw] ??
        new RegExp(
          "\\b" + kw.replace(/[+.]/g, "\\$&").replace(/\//g, "\\/") + "\\b",
          "i",
        );
      if (pat.test(low)) matches.push(kw);
    }
    if (matches.length) found[cat] = matches;
  }

  return found;
}

export function getWordFrequencies(text: string): Map<string, number> {
  const words = (text.toLowerCase().match(/\b[a-z][a-z0-9+#.]*\b/g) ?? [])
    .filter((w) => !STOP_WORDS.has(w) && w.length > 2);
  const freq = new Map<string, number>();
  for (const w of words) {
    freq.set(w, (freq.get(w) ?? 0) + 1);
  }
  return freq;
}

function getWords(text: string): string[] {
  return (text.toLowerCase().match(/\b[a-z][a-z0-9+#.]*\b/g) ?? []).filter(
    (w) => !STOP_WORDS.has(w) && w.length > 2,
  );
}

export function extractNgrams(text: string, n = 2): string[] {
  const words = getWords(text);
  const ngrams: string[] = [];
  for (let i = 0; i < words.length - n + 1; i++) {
    ngrams.push(words.slice(i, i + n).join(" "));
  }
  return ngrams;
}

export function extractNgramsWeighted(
  text: string,
  maxN = 4,
): Map<string, number> {
  const words = getWords(text);
  const counts = new Map<string, number>();
  for (let n = 2; n <= maxN; n++) {
    for (let i = 0; i < words.length - n + 1; i++) {
      const ng = words.slice(i, i + n).join(" ");
      counts.set(ng, (counts.get(ng) ?? 0) + 1);
    }
  }
  return counts;
}

export function jaccardSimilarity(textA: string, textB: string): number {
  const wordsA = new Set(getWords(textA));
  const wordsB = new Set(getWords(textB));
  if (!wordsA.size && !wordsB.size) return 1;
  if (!wordsA.size || !wordsB.size) return 0;
  const intersection = [...wordsA].filter((w) => wordsB.has(w)).length;
  const union = new Set([...wordsA, ...wordsB]).size;
  return intersection / union;
}

export function bm25Score(
  queryTerms: string[],
  docFreq: Map<string, number>,
  docLength: number,
  avgDocLength: number,
  corpusSize = 2,
  docContaining: Map<string, number> = new Map(),
  k1 = 1.5,
  b = 0.75,
): number {
  let score = 0;
  for (const term of queryTerms) {
    const tf = docFreq.get(term) ?? 0;
    const nContaining = docContaining.get(term) ?? 0;
    const idf = Math.log(
      (corpusSize - nContaining + 0.5) / (nContaining + 0.5) + 1,
    );
    if (avgDocLength > 0) {
      const num = tf * (k1 + 1);
      const den = tf + k1 * (1 - b + b * (docLength / avgDocLength));
      score += idf * (num / den);
    }
  }
  return score;
}

export function bm25Similarity(textA: string, textB: string): number {
  const wA = getWords(textA);
  const wB = getWords(textB);
  if (!wA.length && !wB.length) return 1;
  if (!wA.length || !wB.length) return 0;

  const freqA = new Map<string, number>();
  const freqB = new Map<string, number>();
  for (const w of wA) freqA.set(w, (freqA.get(w) ?? 0) + 1);
  for (const w of wB) freqB.set(w, (freqB.get(w) ?? 0) + 1);

  const allWords = new Set([...freqA.keys(), ...freqB.keys()]);
  const lenA = wA.length;
  const lenB = wB.length;
  const avgLen = (lenA + lenB) / 2;

  const docContaining = new Map<string, number>();
  for (const w of allWords) {
    let c = 0;
    if (freqA.has(w)) c++;
    if (freqB.has(w)) c++;
    docContaining.set(w, c);
  }

  const qTerms = [...freqB.keys()];
  const actual = bm25Score(qTerms, freqA, lenA, avgLen, 2, docContaining);
  const maxS = bm25Score(qTerms, freqB, lenB, avgLen, 2, docContaining);
  if (maxS <= 0) return 0;
  return Math.min(1, actual / maxS);
}

export function calculateKeywordDensity(
  text: string,
  keywords: Set<string>,
): KeywordDensityResult {
  const words = text.toLowerCase().match(/\b[a-z][a-z0-9+#.]*\b/g) ?? [];
  const totalWords = words.length;
  if (totalWords === 0) {
    return {
      total_words: 0,
      keyword_mentions: 0,
      density_pct: 0,
      stuffed_keywords: [],
      status: "good",
    };
  }

  let keywordMentions = 0;
  const keywordCounts = new Map<string, number>();
  for (const kw of keywords) {
    const pat =
      SPECIAL_PATTERNS[kw] ??
      new RegExp(
        "\\b" + kw.replace(/[+.]/g, "\\$&").replace(/\//g, "\\/") + "\\b",
        "i",
      );
    const count = (text.toLowerCase().match(new RegExp(pat, "gi")) ?? [])
      .length;
    if (count > 0) {
      keywordCounts.set(kw, count);
      keywordMentions += count;
    }
  }

  const density = (keywordMentions / totalWords) * 100;
  const stuffed = [...keywordCounts.entries()]
    .filter(([, count]) => count > 4)
    .map(([keyword, count]) => ({ keyword, count }));

  return {
    total_words: totalWords,
    keyword_mentions: keywordMentions,
    density_pct: Math.round(density * 10) / 10,
    stuffed_keywords: stuffed,
    status: density <= 8.0 ? "good" : density <= 15.0 ? "warning" : "danger",
  };
}

const YOE_PATTERN =
  /(\d+)\+?\s*(?:[-–]?\s*\d+)?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp\.?|professional)?(?:\s+(?:with|in|using|of)\s+(.+?))?(?:\.|,|;|\n|$)/gi;

export function extractYoeRequirements(jdText: string): YoeRequirement[] {
  const requirements: YoeRequirement[] = [];
  let match: RegExpExecArray | null;
  const pat = new RegExp(YOE_PATTERN.source, YOE_PATTERN.flags);
  while ((match = pat.exec(jdText)) !== null) {
    const years = parseInt(match[1], 10);
    let skill = match[2] ?? null;
    if (skill) skill = skill.trim().replace(/[.,;]+$/, "");
    requirements.push({ years, skill });
  }
  return requirements;
}

const MONTH_TO_NUM: Record<string, number> = {
  jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
  jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12,
};

const MONTH_DATE_RANGE =
  /((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\.*\s*(\d{4})\s*(?:[-–—]+|to)\s*(?:(present|current|now)|((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\.*\s*(\d{4}))/gi;

const YEAR_RANGE_PATTERN =
  /(\d{4})\s*(?:[-–—]+|to)\s*(present|current|now|\d{4})/gi;

export function estimateResumeYoe(
  resumeText: string,
  currentYear?: number,
): ResumeYoe {
  const now = new Date();
  const yearNow = currentYear ?? now.getFullYear();
  const monthNow = now.getMonth() + 1;
  const ranges: [number, number][] = [];

  let match: RegExpExecArray | null;
  const monthPat = new RegExp(MONTH_DATE_RANGE.source, MONTH_DATE_RANGE.flags);
  while ((match = monthPat.exec(resumeText)) !== null) {
    const startMonthStr = match[1].slice(0, 3).toLowerCase();
    const startYear = parseInt(match[2], 10);
    const startFrac = startYear + (MONTH_TO_NUM[startMonthStr] ?? 1 - 1) / 12;

    let endFrac: number;
    if (match[3]) {
      endFrac = yearNow + (monthNow - 1) / 12;
    } else {
      const endMonthStr = match[4].slice(0, 3).toLowerCase();
      const endYear = parseInt(match[5], 10);
      endFrac = endYear + (MONTH_TO_NUM[endMonthStr] ?? 12) / 12;
    }

    if (1970 <= startYear && startYear <= yearNow + 1 && startFrac <= endFrac) {
      ranges.push([startFrac, endFrac]);
    }
  }

  if (ranges.length === 0) {
    const yearPat = new RegExp(
      YEAR_RANGE_PATTERN.source,
      YEAR_RANGE_PATTERN.flags,
    );
    while ((match = yearPat.exec(resumeText)) !== null) {
      const startYear = parseInt(match[1], 10);
      const endStr = match[2].toLowerCase();
      const endYear =
        endStr === "present" || endStr === "current" || endStr === "now"
          ? yearNow
          : parseInt(endStr, 10);
      if (
        1970 <= startYear &&
        startYear <= yearNow + 1 &&
        startYear <= endYear
      ) {
        ranges.push([startYear, endYear]);
      }
    }
  }

  if (ranges.length === 0) {
    return { total_years: 0, date_ranges: [], has_dates: false };
  }

  ranges.sort((a, b) => a[0] - b[0]);
  const merged: [number, number][] = [ranges[0]];
  for (const [start, end] of ranges.slice(1)) {
    const last = merged[merged.length - 1];
    if (start <= last[1]) {
      merged[merged.length - 1] = [last[0], Math.max(last[1], end)];
    } else {
      merged.push([start, end]);
    }
  }

  const totalFrac = merged.reduce((sum, [s, e]) => sum + (e - s), 0);
  return {
    total_years: Math.round(totalFrac),
    date_ranges: merged.map(([s, e]) => [Math.round(s), Math.round(e)]),
    has_dates: true,
  };
}

export function segmentResume(text: string): Record<string, string> {
  const bounds: [number, string][] = [];
  for (const [name, pat] of Object.entries(SECTION_HEADERS)) {
    const m = pat.exec(text);
    if (m) bounds.push([m.index, name]);
  }
  if (!bounds.length) return { other: text };

  bounds.sort((a, b) => a[0] - b[0]);
  const secs: Record<string, string> = {};
  if (bounds[0][0] > 0) secs.other = text.slice(0, bounds[0][0]);
  for (let i = 0; i < bounds.length; i++) {
    const end = i + 1 < bounds.length ? bounds[i + 1][0] : text.length;
    secs[bounds[i][1]] = text.slice(bounds[i][0], end);
  }
  return secs;
}

export function scoreToGrade(score: number): string {
  if (score >= 85) return "A";
  if (score >= 75) return "B";
  if (score >= 60) return "C";
  if (score >= 45) return "D";
  return "F";
}

export function analyzeSections(resumeText: string): SectionAnalysis {
  return {
    contact: /email|phone|@|\d{3}/.test(resumeText),
    education:
      /(?:^|\n)\s*(?:education|university|college|degree|bachelor|master)/m.test(
        resumeText,
      ),
    experience:
      /(?:^|\n)\s*(?:experience|work\s+history|employment|professional\s+experience)/m.test(
        resumeText,
      ),
    projects:
      /(?:^|\n)\s*(?:projects?|personal\s+projects?|academic\s+projects?)/m.test(
        resumeText,
      ),
    skills:
      /(?:^|\n)\s*(?:skills?|technical\s+skills?|core\s+competencies)/m.test(
        resumeText,
      ),
    summary:
      /(?:^|\n)\s*(?:summary|objective|professional\s+summary|profile|about\s+me)/m.test(
        resumeText,
      ),
  };
}

const REQUIREMENT_SIGNALS =
  /(?:experience\s+(?:with|in|using)|proficien(?:t|cy)\s+(?:with|in)|knowledge\s+of|familiar(?:ity)?\s+with|expertise\s+(?:in|with)|(?:must|should)\s+(?:have|know)|required|preferred|nice\s+to\s+have|skills?\s*:)\s+(.+?)(?:\.|,|;|\n|$)/gi;

const BULLET_PATTERN = /(?:^|\n)\s*(?:[-*+]|\d+[.)]\s)\s*(.+?)(?:\n|$)/g;

function cleanJdMarkup(text: string): string {
  text = text.replace(/`([^`]*)`/g, "$1");
  text = text.replace(/\*{1,3}([^*]+)\*{1,3}/g, "$1");
  text = text.replace(/#{1,6}\s*/g, "");
  text = text.replace(/\[\d+(?:\s*,\s*\d+)*\]/g, "");
  return text;
}

export function extractDynamicKeywords(
  jdText: string,
  taxonomyKws: Set<string>,
): string[] {
  jdText = cleanJdMarkup(jdText);
  const candidates = new Set<string>();

  let m: RegExpExecArray | null;
  const reqPat = new RegExp(
    REQUIREMENT_SIGNALS.source,
    REQUIREMENT_SIGNALS.flags,
  );
  while ((m = reqPat.exec(jdText)) !== null) {
    const phrase = m[1].trim();
    for (const term of phrase.split(/,\s*|\s+and\s+|\s+or\s+/)) {
      const t = term
        .trim()
        .toLowerCase()
        .replace(/[^\w\s+#./\-]/g, "")
        .trim();
      if (
        t.length > 2 &&
        t.split(/\s+/).length <= 3 &&
        !STOP_WORDS.has(t) &&
        !taxonomyKws.has(t)
      ) {
        candidates.add(t);
      }
    }
  }

  const capPat = /\b([A-Z][a-zA-Z0-9+#.]*(?:\s+[A-Z][a-zA-Z0-9]*)*)\b/g;
  while ((m = capPat.exec(jdText)) !== null) {
    const t = m[1].trim();
    const tl = t.toLowerCase();
    const pos = m.index;
    const isSentStart =
      pos === 0 ||
      ".!?\n".includes(jdText[pos - 1]) ||
      (pos >= 2 && jdText.slice(pos - 2, pos) === ". ");
    if (
      tl.length > 2 &&
      !STOP_WORDS.has(tl) &&
      !taxonomyKws.has(tl) &&
      !isSentStart
    ) {
      candidates.add(tl);
    }
  }

  const bulletPat = new RegExp(BULLET_PATTERN.source, BULLET_PATTERN.flags);
  while ((m = bulletPat.exec(jdText)) !== null) {
    const line = m[1].trim();
    for (const w of line.split(/,\s*|\s+and\s+/)) {
      const t = w
        .trim()
        .toLowerCase()
        .replace(/[^\w\s+#./\-]/g, "")
        .trim();
      if (
        t.length > 2 &&
        !STOP_WORDS.has(t) &&
        !taxonomyKws.has(t) &&
        t.split(/\s+/).length <= 3
      ) {
        candidates.add(t);
      }
    }
  }

  return [...candidates].sort();
}

export function computeMatch(
  resumeText: string,
  jdText: string,
  resumeRaw = "",
  jdRaw = "",
): MatchResult {
  const resumeLower = normalizeText(resumeText.toLowerCase());
  const jdLower = normalizeText(jdText.toLowerCase());
  const resumeOriginal = resumeRaw || resumeText;
  const jdOriginal = jdRaw || jdText;

  const jdKeywords = extractKeywords(jdLower);
  const resumeKeywords = extractKeywords(resumeLower);

  const jdFlat = new Set(Object.values(jdKeywords).flat());
  const resumeFlat = new Set(Object.values(resumeKeywords).flat());

  const matched = new Set([...jdFlat].filter((k) => resumeFlat.has(k)));
  const missing = new Set([...jdFlat].filter((k) => !resumeFlat.has(k)));

  const resumeSections = segmentResume(resumeOriginal.toLowerCase());
  let totalWeight = 0;
  let matchedWeight = 0;
  const kwPlacement: KeywordPlacement = {};

  for (const [category, data] of Object.entries(SKILL_TAXONOMY)) {
    const jdCatKws = new Set(jdKeywords[category] ?? []);
    if (jdCatKws.size) {
      totalWeight += jdCatKws.size * data.weight;
      for (const kw of jdCatKws) {
        let bestMultiplier = 0;
        let bestSection: string | null = null;
        for (const [sectionName, sectionText] of Object.entries(
          resumeSections,
        )) {
          const pat =
            SPECIAL_PATTERNS[kw] ??
            new RegExp(
              "\\b" +
                kw.replace(/[+.]/g, "\\$&").replace(/\//g, "\\/") +
                "\\b",
              "i",
            );
          if (pat.test(sectionText)) {
            const mult = SECTION_MULTIPLIERS[sectionName] ?? 1.0;
            if (mult > bestMultiplier) {
              bestMultiplier = mult;
              bestSection = sectionName;
            }
          }
        }
        if (bestMultiplier > 0) {
          matchedWeight += data.weight * Math.min(bestMultiplier, 1.5);
          if (bestSection) {
            if (!kwPlacement[bestSection]) kwPlacement[bestSection] = [];
            kwPlacement[bestSection].push(kw);
          }
        }
      }
    }
  }

  let finalScore: number;
  let textScore: number;

  if (!resumeLower.trim() && !jdLower.trim()) {
    finalScore = 0;
    textScore = 0;
  } else {
    const keywordScore =
      totalWeight > 0
        ? Math.min(100, (matchedWeight / totalWeight) * 100)
        : 0;
    textScore = bm25Similarity(resumeLower, jdLower) * 100;

    const allTaxKws = new Set(
      Object.values(SKILL_TAXONOMY).flatMap((d) => [...d.keywords]),
    );
    const dynamicJdKwsEarly = extractDynamicKeywords(jdOriginal, allTaxKws);
    const dynamicMatchedEarly = dynamicJdKwsEarly.filter((k) => {
      const escaped = normalizeText(k).replace(/[+.]/g, "\\$&");
      return new RegExp("\\b" + escaped + "\\b", "i").test(resumeLower);
    });

    const dynScore = dynamicJdKwsEarly.length
      ? (dynamicMatchedEarly.length / dynamicJdKwsEarly.length) * 100
      : 0;

    if (totalWeight > 0) {
      if (dynamicJdKwsEarly.length) {
        finalScore =
          0.7 * keywordScore + 0.2 * textScore + 0.1 * dynScore;
      } else {
        finalScore = 0.8 * keywordScore + 0.2 * textScore;
      }
    } else {
      finalScore = textScore;
    }
    finalScore = Math.min(100, finalScore);
  }

  const matchedByCat: KeywordsByCategory = {};
  const missingByCat: KeywordsByCategory = {};
  for (const cat of Object.keys(SKILL_TAXONOMY)) {
    const jCat = new Set(jdKeywords[cat] ?? []);
    const rCat = new Set(resumeKeywords[cat] ?? []);
    const m = [...jCat].filter((k) => rCat.has(k)).sort();
    const x = [...jCat].filter((k) => !rCat.has(k)).sort();
    if (m.length) matchedByCat[cat] = m;
    if (x.length) missingByCat[cat] = x;
  }

  const jdNg = extractNgramsWeighted(jdLower, 4);
  const rNg = extractNgramsWeighted(resumeLower, 4);
  const missingPhrases = [...jdNg.keys()]
    .filter(
      (p) => !rNg.has(p) && !p.split(" ").some((w) => STOP_WORDS.has(w)),
    )
    .sort((a, b) => {
      const la = a.split(" ").length;
      const lb = b.split(" ").length;
      if (lb !== la) return lb - la;
      return (jdNg.get(b) ?? 0) - (jdNg.get(a) ?? 0);
    })
    .slice(0, 10);

  const bonusSkills = [...resumeFlat]
    .filter((k) => !jdFlat.has(k))
    .sort()
    .slice(0, 15);

  const allTaxKws = new Set(
    Object.values(SKILL_TAXONOMY).flatMap((d) => [...d.keywords]),
  );
  const dynamicJdKeywords = extractDynamicKeywords(jdOriginal, allTaxKws);
  const dynamicMatched = dynamicJdKeywords.filter((k) => {
    const escaped = normalizeText(k).replace(/[+.]/g, "\\$&");
    return new RegExp("\\b" + escaped + "\\b", "i").test(resumeLower);
  });
  const dynamicMissing = dynamicJdKeywords.filter(
    (k) => !dynamicMatched.includes(k),
  );

  const grade = scoreToGrade(finalScore);
  const sections = analyzeSections(resumeOriginal.toLowerCase());

  return {
    score: Math.round(finalScore * 10) / 10,
    grade,
    matched_count: matched.size,
    missing_count: missing.size,
    total_jd_keywords: jdFlat.size,
    matched_by_category: matchedByCat,
    missing_by_category: missingByCat,
    missing_phrases: missingPhrases,
    bonus_skills: bonusSkills,
    sections,
    jd_keyword_count: jdFlat.size,
    resume_keyword_count: resumeFlat.size,
    text_similarity:
      resumeLower.trim() || jdLower.trim()
        ? Math.round(textScore * 10) / 10
        : 0,
    dynamic_jd_keywords: dynamicJdKeywords,
    dynamic_matched: dynamicMatched,
    dynamic_missing: dynamicMissing,
    keyword_placement: kwPlacement,
    yoe_requirements: extractYoeRequirements(jdOriginal),
    resume_yoe: estimateResumeYoe(resumeOriginal),
    keyword_density: calculateKeywordDensity(
      resumeLower,
      new Set([...resumeFlat, ...matched]),
    ),
  };
}
