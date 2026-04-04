import type { MatchResult } from "@ats-scanner/core";
import { SKILL_TAXONOMY } from "@ats-scanner/core";

const SECTION_ICONS: Record<string, string> = {
  contact: "📧", education: "🎓", experience: "💼",
  projects: "🚀", skills: "⚡", summary: "📝",
};

function scoreColor(s: number): string {
  return s >= 75 ? "var(--green)" : s >= 55 ? "var(--yellow)" : "var(--red)";
}

function scoreMsg(s: number): [string, string] {
  if (s >= 85) return ["Excellent Match!", "Your resume strongly aligns with this job. You're a competitive candidate — apply with confidence."];
  if (s >= 75) return ["Good Match", "Strong alignment with a few gaps. Address the missing keywords to improve your chances."];
  if (s >= 60) return ["Moderate Match", "Worth applying, but tailor your resume with more of the missing keywords before submitting."];
  if (s >= 45) return ["Weak Match", "Significant keyword gaps found. Consider whether this role fits your current profile."];
  return ["Low Match", "Your resume is missing many key requirements. Focus on roles that better match your skill set."];
}

function renderKws(
  containerId: string,
  byCat: Record<string, string[]>,
  tagClass: string,
  emptyMsg: string,
): void {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!Object.keys(byCat).length) {
    el.innerHTML = `<div class="no-items">${emptyMsg}</div>`;
    return;
  }
  const taxonomy = SKILL_TAXONOMY as Record<string, { keywords: readonly string[]; weight: number }>;
  el.innerHTML = Object.entries(byCat)
    .map(([cat, kws]) => {
      const catData = taxonomy[cat];
      const icon = catData ? getCatIcon(cat) : "·";
      const label = catData ? getCatLabel(cat) : cat;
      return `<div class="cat-block">
        <div class="cat-label">${icon} ${label}</div>
        <div class="tags-row">${kws.map((k, i) => `<span class="tag ${tagClass}" style="animation-delay:${i * 0.04}s">${k}</span>`).join("")}</div>
      </div>`;
    })
    .join("");
}

const CAT_META: Record<string, [string, string]> = {
  languages: ["💻", "Languages"],
  frameworks: ["⚙️", "Frameworks & Libraries"],
  databases: ["🗄️", "Databases"],
  devops_cloud: ["☁️", "DevOps & Cloud"],
  tools: ["🔧", "Tools & Platforms"],
  concepts: ["🧠", "Concepts & Practices"],
  soft_skills: ["🤝", "Soft Skills"],
  education: ["🎓", "Education"],
};

function getCatIcon(cat: string): string { return CAT_META[cat]?.[0] ?? "·"; }
function getCatLabel(cat: string): string { return CAT_META[cat]?.[1] ?? cat; }

function generateRecs(r: MatchResult): string[] {
  const recs: string[] = [];
  const { score, missing_by_category: missingByCat, sections, bonus_skills: bonusSkills, dynamic_missing: dynamicMissing, keyword_placement: kwPlacement } = r;

  if (score < 50) recs.push(`<strong>Critical:</strong> Your resume matches only ${score.toFixed(0)}% of this JD. Focus on adding the top missing keywords from each category.`);

  for (const cat of ["languages", "frameworks", "databases", "devops_cloud"]) {
    if (missingByCat[cat]?.length) {
      const kws = missingByCat[cat].slice(0, 3).join(", ");
      const name = getCatLabel(cat);
      recs.push(
        `<strong>${name}:</strong> Missing <em>${kws}</em>. ${!sections.skills ? "Add to Skills AND Experience for max ATS weight." : "Add these to your Skills section explicitly."}`,
      );
    }
  }

  if (!sections.summary) recs.push("<strong>Add a Summary:</strong> A professional summary lets you front-load 4-6 core keywords. ATS systems weight summary keywords highly.");
  if (!sections.skills) recs.push("<strong>Add a Skills Section:</strong> A dedicated Skills section gets a 1.5x weight multiplier in most ATS systems.");
  if (!sections.projects && score < 75) recs.push("<strong>Add Projects:</strong> A Projects section lets you demonstrate skills with context. \"Built X using Python and React\" scores higher than just listing them.");

  if (kwPlacement) {
    const skillsKws = new Set(kwPlacement.skills ?? []);
    const expKws = new Set(kwPlacement.experience ?? []);
    const onlySkills = [...skillsKws].filter((k) => !expKws.has(k));
    if (onlySkills.length > 2) recs.push(`<strong>Prove Your Skills:</strong> <em>${onlySkills.slice(0, 3).join(", ")}</em> appear only in Skills. Mention them in Experience bullets too — ATS rewards the "Claim + Proof" pattern.`);
  }

  if (dynamicMissing?.length > 2) recs.push(`<strong>JD-Specific Terms:</strong> The JD mentions <em>${dynamicMissing.slice(0, 3).join(", ")}</em> which aren't standard keywords. If you have experience, add them.`);

  if (score >= 85) recs.push("<strong>Excellent Match:</strong> Strong alignment! Focus your cover letter on the 1-2 remaining gaps.");
  else if (score >= 75) recs.push("<strong>Good Match:</strong> Solid foundation. Address the missing keywords above for top-tier ATS scoring.");

  if (!recs.length) recs.push("<strong>Well Optimized:</strong> Your resume is well-aligned. Focus on quantifying achievements in your bullet points.");
  return recs;
}

export function renderResults(result: MatchResult): void {
  document.getElementById("results")!.style.display = "block";

  const circ = 2 * Math.PI * 40;
  const offset = circ - (result.score / 100) * circ;
  const col = scoreColor(result.score);
  const ring = document.getElementById("scoreRing") as unknown as SVGCircleElement;
  ring.style.stroke = col;
  setTimeout(() => { ring.style.strokeDashoffset = String(offset); }, 80);

  document.getElementById("scorePct")!.textContent = result.score + "%";
  (document.getElementById("scorePct") as HTMLElement).style.color = col;
  document.getElementById("scoreGrade")!.textContent = "Grade " + result.grade;

  const [title, msg] = scoreMsg(result.score);
  document.getElementById("scoreTitle")!.textContent = title;
  document.getElementById("scoreMsg")!.textContent = msg;
  (document.getElementById("progFill") as HTMLElement).style.width = result.score + "%";
  (document.getElementById("progFill") as HTMLElement).style.background = col;

  document.getElementById("scorePills")!.innerHTML = `
    <span class="pill pill-g">✓ ${result.matched_count} matched</span>
    <span class="pill pill-r">✗ ${result.missing_count} missing</span>
    ${result.bonus_skills.length ? `<span class="pill pill-b">+ ${result.bonus_skills.length} bonus</span>` : ""}
    <span class="pill pill-o">Grade ${result.grade}</span>`;

  document.getElementById("qsTotal")!.textContent = String(result.total_jd_keywords);
  document.getElementById("qsMatched")!.textContent = String(result.matched_count);
  document.getElementById("qsMissing")!.textContent = String(result.missing_count);
  document.getElementById("matchedCount")!.textContent = String(result.matched_count);
  document.getElementById("missingCount")!.textContent = String(result.missing_count);
  document.getElementById("bonusCount")!.textContent = String(result.bonus_skills.length);

  renderKws("matchedBody", result.matched_by_category, "tag-match", "No matched keywords found.");
  renderKws("missingBody", result.missing_by_category, "tag-miss", "No missing keywords — great!");

  const bonusEl = document.getElementById("bonusBody")!;
  if (result.bonus_skills.length) {
    bonusEl.innerHTML = `<div class="tags-row">${result.bonus_skills.map((k, i) => `<span class="tag tag-bonus" style="animation-delay:${i * 0.03}s">${k}</span>`).join("")}</div>`;
  } else {
    bonusEl.innerHTML = '<div class="no-items">No bonus skills found.</div>';
  }

  document.getElementById("sectionsBody")!.innerHTML = `<div class="section-grid">
    ${Object.entries(result.sections).map(([k, v]) => `
      <div class="sec-item ${v ? "ok" : "miss"}">
        <span class="sec-icon">${SECTION_ICONS[k] ?? "·"}</span>
        <span style="font-size:12px">${k.charAt(0).toUpperCase() + k.slice(1)}</span>
        <span class="sec-status ${v ? "ok" : "miss"}">${v ? "✓ Found" : "✗ Missing"}</span>
      </div>`).join("")}
  </div>`;

  const phEl = document.getElementById("phrasesBody")!;
  document.getElementById("phrasesCount")!.textContent = String(result.missing_phrases.length);
  if (result.missing_phrases.length) {
    phEl.innerHTML = result.missing_phrases.map((p) => `<div class="phrase-item">${p}</div>`).join("");
  } else {
    phEl.innerHTML = '<div class="no-items">No key phrases missing — great match!</div>';
  }

  const recs = generateRecs(result);
  document.getElementById("recsBody")!.innerHTML = recs
    .map((r, i) => `<div class="rec-item" style="animation-delay:${i * 0.07}s"><div class="rec-num">${i + 1}.</div><div class="rec-text">${r}</div></div>`)
    .join("");

  document.getElementById("results")!.scrollIntoView({ behavior: "smooth", block: "start" });
}
