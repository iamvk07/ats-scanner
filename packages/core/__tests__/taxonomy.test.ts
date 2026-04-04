import { describe, it, expect } from "vitest";
import { SKILL_TAXONOMY, SYNONYM_MAP } from "../src/index.js";

describe("TaxonomyValidation", () => {
  it("has no cross-category duplicate keywords", () => {
    const seen = new Map<string, string>();
    for (const [cat, data] of Object.entries(SKILL_TAXONOMY)) {
      for (const kw of data.keywords) {
        expect(seen.has(kw)).toBe(false);
        seen.set(kw, cat);
      }
    }
  });

  it("has expected minimum keyword count", () => {
    const total = Object.values(SKILL_TAXONOMY).reduce(
      (sum, d) => sum + d.keywords.length,
      0,
    );
    expect(total).toBeGreaterThanOrEqual(197);
  });

  it("has no alias-taxonomy overlap", () => {
    const allKws = new Set(
      Object.values(SKILL_TAXONOMY).flatMap((d) => [...d.keywords]),
    );
    for (const [alias, canonical] of Object.entries(SYNONYM_MAP)) {
      const bothInTaxonomy = allKws.has(alias) && allKws.has(canonical);
      expect(bothInTaxonomy).toBe(false);
    }
  });

  it("all categories have positive weights", () => {
    for (const [, data] of Object.entries(SKILL_TAXONOMY)) {
      expect(data.weight).toBeGreaterThan(0);
    }
  });

  it("all synonym targets exist in taxonomy", () => {
    const allKws = new Set(
      Object.values(SKILL_TAXONOMY).flatMap((d) => [...d.keywords]),
    );
    for (const [, canonical] of Object.entries(SYNONYM_MAP)) {
      expect(allKws.has(canonical)).toBe(true);
    }
  });
});
