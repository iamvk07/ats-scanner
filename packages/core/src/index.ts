export type {
  MatchResult,
  KeywordsByCategory,
  KeywordPlacement,
  KeywordDensityResult,
  StuffedKeyword,
  YoeRequirement,
  ResumeYoe,
  SectionAnalysis,
  TaxonomyCategory,
  SkillTaxonomy,
} from "./types.js";

export {
  SKILL_TAXONOMY,
  SYNONYM_MAP,
  SORTED_SYNONYMS,
  STOP_WORDS,
  SPECIAL_PATTERNS,
  SECTION_MULTIPLIERS,
  SECTION_HEADERS,
} from "./taxonomy.js";

export {
  normalizeText,
  extractKeywords,
  getWordFrequencies,
  extractNgrams,
  extractNgramsWeighted,
  jaccardSimilarity,
  bm25Score,
  bm25Similarity,
  calculateKeywordDensity,
  extractYoeRequirements,
  estimateResumeYoe,
  segmentResume,
  scoreToGrade,
  analyzeSections,
  extractDynamicKeywords,
  computeMatch,
} from "./analyzer.js";

export { cleanText, stripLatex } from "./extractor.js";
