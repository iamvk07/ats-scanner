import { computeMatch, cleanText } from "@ats-scanner/core";
import type { MatchResult } from "@ats-scanner/core";

export function runAnalysis(resumeText: string, jdText: string): MatchResult {
  const rc = cleanText(resumeText);
  const jc = cleanText(jdText);
  return computeMatch(rc, jc, resumeText, jdText);
}
