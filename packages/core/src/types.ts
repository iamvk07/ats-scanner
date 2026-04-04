export interface TaxonomyCategory {
  weight: number;
  keywords: readonly string[];
}

export type SkillTaxonomy = Record<string, TaxonomyCategory>;

export interface KeywordsByCategory {
  [category: string]: string[];
}

export interface KeywordPlacement {
  [section: string]: string[];
}

export interface KeywordDensityResult {
  total_words: number;
  keyword_mentions: number;
  density_pct: number;
  stuffed_keywords: StuffedKeyword[];
  status: "good" | "warning" | "danger";
}

export interface StuffedKeyword {
  keyword: string;
  count: number;
}

export interface YoeRequirement {
  years: number;
  skill: string | null;
}

export interface ResumeYoe {
  total_years: number;
  date_ranges: [number, number][];
  has_dates: boolean;
}

export interface SectionAnalysis {
  contact: boolean;
  education: boolean;
  experience: boolean;
  projects: boolean;
  skills: boolean;
  summary: boolean;
}

export interface MatchResult {
  score: number;
  grade: string;
  matched_count: number;
  missing_count: number;
  total_jd_keywords: number;
  matched_by_category: KeywordsByCategory;
  missing_by_category: KeywordsByCategory;
  missing_phrases: string[];
  bonus_skills: string[];
  sections: SectionAnalysis;
  jd_keyword_count: number;
  resume_keyword_count: number;
  text_similarity: number;
  dynamic_jd_keywords: string[];
  dynamic_matched: string[];
  dynamic_missing: string[];
  keyword_placement: KeywordPlacement;
  yoe_requirements: YoeRequirement[];
  resume_yoe: ResumeYoe;
  keyword_density: KeywordDensityResult;
}
