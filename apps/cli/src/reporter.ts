import pc from "picocolors";
import type { MatchResult } from "@ats-scanner/core";

const WIDTH = 72;

const USE_COLOR =
  process.env.FORCE_COLOR !== undefined ||
  (process.stdout.isTTY ?? false);

function col(text: string, colorFn: (s: string) => string): string {
  return USE_COLOR ? colorFn(String(text)) : String(text);
}

function stripAnsi(text: string): string {
  return text.replace(/\x1b\[[0-9;]*m/g, "");
}

function headerLine(char = "═", width = WIDTH): string {
  return col(char.repeat(width), pc.cyan);
}

function sectionLine(char = "─", width = WIDTH): string {
  return col(char.repeat(width), pc.dim);
}

function center(text: string, width = WIDTH): string {
  const clean = stripAnsi(text);
  const pad = Math.max(0, Math.floor((width - clean.length) / 2));
  return " ".repeat(pad) + text;
}

function label(text: string, width = 20): string {
  return col(text.padEnd(width), pc.dim);
}

function scoreBar(score: number, width = 40): string {
  const filled = Math.round((score / 100) * width);
  const empty = width - filled;
  const barColor = score >= 75 ? pc.green : score >= 55 ? pc.yellow : pc.red;
  return "[" + col("█".repeat(filled), barColor) + col("░".repeat(empty), pc.dim) + "]";
}

function scoreColor(score: number): (s: string) => string {
  if (score >= 75) return pc.green;
  if (score >= 55) return pc.yellow;
  return pc.red;
}

function gradeBadge(grade: string): string {
  if (!USE_COLOR) return `[${grade}]`;
  const bgMap: Record<string, (s: string) => string> = {
    A: pc.bgGreen,
    B: pc.bgBlue,
    C: pc.bgYellow,
    D: pc.bgRed,
    F: pc.bgRed,
  };
  const bg = bgMap[grade] ?? pc.bgBlack;
  return bg(pc.bold(` ${grade} `));
}

function tagMatched(kw: string): string {
  return col(` ✓ ${kw} `, pc.green);
}

function tagMissing(kw: string): string {
  return col(` ✗ ${kw} `, pc.red);
}

function tagBonus(kw: string): string {
  return col(` + ${kw} `, pc.blue);
}

function wrapTags(tags: string[], width = WIDTH - 4): string[] {
  const lines: string[] = [];
  let current = "  ";
  for (const tag of tags) {
    const clean = stripAnsi(current);
    const tagClean = stripAnsi(tag);
    if (clean.length + tagClean.length > width) {
      lines.push(current);
      current = "  " + tag;
    } else {
      current += tag;
    }
  }
  if (current.trim()) lines.push(current);
  return lines;
}

const CAT_DISPLAY: Record<string, [string, string]> = {
  languages: ["💻", "Programming Languages"],
  frameworks: ["⚙️ ", "Frameworks & Libraries"],
  databases: ["🗄️ ", "Databases"],
  devops_cloud: ["☁️ ", "DevOps & Cloud"],
  tools: ["🔧", "Tools & Platforms"],
  concepts: ["🧠", "Concepts & Practices"],
  soft_skills: ["🤝", "Soft Skills"],
  education: ["🎓", "Education"],
};

export function setColorEnabled(enabled: boolean): void {
  (globalThis as Record<string, unknown>).__atsColorOverride = enabled;
}

function isColorEnabled(): boolean {
  const override = (globalThis as Record<string, unknown>).__atsColorOverride;
  if (typeof override === "boolean") return override;
  return USE_COLOR;
}

export function printReport(
  result: MatchResult,
  resumeName = "resume",
  jdName = "job description",
): string[] {
  const { score, grade } = result;
  const lines: string[] = [];

  const colorEnabled = isColorEnabled();
  const c = (text: string, colorFn: (s: string) => string) =>
    colorEnabled ? colorFn(String(text)) : String(text);

  const p = (text = ""): void => {
    console.log(text);
    lines.push(text);
  };

  p();
  p(headerLine());
  p(center(c("  ATS SCANNER  ", (s) => pc.bold(pc.cyan(s)))));
  p(center(c("Resume vs Job Description Analyzer", pc.dim)));
  p(center(c("by calebe94  ·  github.com/Calebe94/ats-scanner", pc.dim)));
  p(headerLine());
  p();

  p(`  ${label("Resume:")}  ${c(resumeName, pc.white)}`);
  p(`  ${label("Job Description:")}  ${c(jdName, pc.white)}`);
  p(`  ${label("Analyzed:")}  ${c(new Date().toISOString().slice(0, 16).replace("T", " "), pc.dim)}`);
  p();

  p(sectionLine());
  p(`  ${c("MATCH SCORE", pc.bold)}`);
  p(sectionLine());
  p();

  const sColor = scoreColor(score);
  p(`  ${c(`${score.toFixed(1)}%`, (s) => pc.bold(sColor(s)))}  ${scoreBar(score)}  ${gradeBadge(grade)}`);
  p();

  if (score >= 85) p(c("  ✦ Excellent match — strong candidate for this role", pc.green));
  else if (score >= 75) p(c("  ✦ Good match — a few gaps to address", pc.green));
  else if (score >= 60) p(c("  ◈ Moderate match — worth applying but tailor your resume", pc.yellow));
  else if (score >= 45) p(c("  ◈ Weak match — significant keyword gaps found", pc.yellow));
  else p(c("  ✗ Poor match — consider different roles or major resume revision", pc.red));
  p();

  p(`  ${label("JD Keywords Found:")}  ${c(String(result.total_jd_keywords), pc.white)}`);
  p(`  ${label("Matched:")}  ${c(String(result.matched_count), pc.green)}  ${label("Missing:")}  ${c(String(result.missing_count), pc.red)}`);
  p();

  if (Object.keys(result.matched_by_category).length) {
    p(sectionLine());
    p(`  ${c("✓ MATCHED KEYWORDS", (s) => pc.bold(pc.green(s)))}  ${c(`(${result.matched_count} found in your resume)`, pc.dim)}`);
    p(sectionLine());
    p();
    for (const [cat, keywords] of Object.entries(result.matched_by_category)) {
      const [icon, name] = CAT_DISPLAY[cat] ?? ["·", cat.replace(/_/g, " ")];
      p(`  ${icon}  ${c(name, pc.bold)}`);
      for (const tl of wrapTags(keywords.map(tagMatched))) p(tl);
      p();
    }
  }

  if (Object.keys(result.missing_by_category).length) {
    p(sectionLine());
    p(`  ${c("✗ MISSING KEYWORDS", (s) => pc.bold(pc.red(s)))}  ${c(`(${result.missing_count} not found in your resume)`, pc.dim)}`);
    p(sectionLine());
    p();
    p(c("  Add these to your resume where applicable:", pc.dim));
    p();
    for (const [cat, keywords] of Object.entries(result.missing_by_category)) {
      const [icon, name] = CAT_DISPLAY[cat] ?? ["·", cat.replace(/_/g, " ")];
      p(`  ${icon}  ${c(name, pc.bold)}`);
      for (const tl of wrapTags(keywords.map(tagMissing))) p(tl);
      p();
    }
  }

  if (result.missing_phrases.length) {
    p(sectionLine());
    p(`  ${c("◈ KEY PHRASES FROM JD NOT IN RESUME", (s) => pc.bold(pc.yellow(s)))}`);
    p(sectionLine());
    p();
    p(c("  Consider naturally incorporating these phrases:", pc.dim));
    p();
    for (const phrase of result.missing_phrases.slice(0, 8)) {
      p(`    ${c("→", pc.yellow)}  ${phrase}`);
    }
    p();
  }

  const dynamicMissing = result.dynamic_missing;
  const dynamicMatched = result.dynamic_matched;
  if (dynamicMissing.length || dynamicMatched.length) {
    p(sectionLine());
    p(`  ${c("⚡ ADDITIONAL JD REQUIREMENTS", (s) => pc.bold(pc.yellow(s)))}`);
    p(sectionLine());
    p();
    p(c("  Terms from the JD not in our standard taxonomy:", pc.dim));
    p();
    for (const kw of dynamicMatched.slice(0, 10)) {
      p(`    ${c("✓", pc.green)}  ${kw}  (${c("found", pc.green)})`);
    }
    for (const kw of dynamicMissing.slice(0, 10)) {
      p(`    ${c("✗", pc.red)}  ${kw}  (${c("missing", pc.red)})`);
    }
    p();
  }

  if (result.bonus_skills.length) {
    p(sectionLine());
    p(`  ${c("+ BONUS SKILLS", (s) => pc.bold(pc.blue(s)))}  ${c("(in your resume but not required by JD)", pc.dim)}`);
    p(sectionLine());
    p();
    for (const tl of wrapTags(result.bonus_skills.map(tagBonus))) p(tl);
    p();
  }

  const yoeReqs = result.yoe_requirements;
  const resumeYoe = result.resume_yoe;
  if (yoeReqs.length) {
    p(sectionLine());
    p(`  ${c("YEARS OF EXPERIENCE CHECK", pc.bold)}`);
    p(sectionLine());
    p();
    if (resumeYoe.has_dates) {
      p(`  ${label("Estimated YoE:")}  ${c(`~${resumeYoe.total_years} years`, pc.white)}`);
    } else {
      p(`  ${label("Estimated YoE:")}  ${c("Could not detect date ranges", pc.yellow)}`);
    }
    p();
    for (const req of yoeReqs) {
      const skillStr = req.skill ? ` of ${req.skill}` : "";
      const reqStr = `${req.years}+ years${skillStr}`;
      if (resumeYoe.has_dates && resumeYoe.total_years >= req.years) {
        p(`    ${c("PASS", pc.green)}  ${reqStr}`);
      } else {
        p(`    ${c("WARN", pc.yellow)}  ${reqStr}`);
      }
    }
    p();
  }

  p(sectionLine());
  p(`  ${c("RESUME SECTION CHECK", pc.bold)}`);
  p(sectionLine());
  p();
  for (const [sectionName, present] of Object.entries(result.sections)) {
    const icon = present ? c("✓", pc.green) : c("✗", pc.red);
    const status = present ? c("Found", pc.green) : c("Not detected", pc.red);
    p(`    ${icon}  ${sectionName.charAt(0).toUpperCase() + sectionName.slice(1).padEnd(15)}  ${status}`);
  }
  p();

  const density = result.keyword_density;
  if (density.total_words > 0) {
    p(sectionLine());
    p(`  ${c("KEYWORD DENSITY", pc.bold)}`);
    p(sectionLine());
    p();
    const pct = density.density_pct;
    let dColor: (s: string) => string;
    let dMsg: string;
    if (density.status === "good") {
      dColor = pc.green;
      dMsg = "Healthy density";
    } else if (density.status === "warning") {
      dColor = pc.yellow;
      dMsg = "Slightly high — review for natural flow";
    } else {
      dColor = pc.red;
      dMsg = "Too high — ATS may flag as keyword stuffing";
    }
    p(`  ${label("Density:")}  ${c(`${pct}%`, dColor)}  (${dMsg})`);
    p(`  ${label("Optimal range:")}  ${c("3-8%", pc.dim)}`);
    if (density.stuffed_keywords.length) {
      p();
      p(c("  Over-repeated keywords (>4 times):", pc.yellow));
      for (const item of density.stuffed_keywords) {
        p(`    ${c("!", pc.yellow)}  ${item.keyword} (${item.count}x)`);
      }
    }
    p();
  }

  p(sectionLine());
  p(`  ${c("RECOMMENDATIONS", pc.bold)}`);
  p(sectionLine());
  p();
  const recs = generateRecommendations(result);
  recs.forEach((rec, i) => {
    p(`  ${c(String(i + 1), (s) => pc.bold(pc.cyan(s)))}.  ${rec}`);
    p();
  });

  p(headerLine());
  p(center(c("ATS Scanner  ·  github.com/Calebe94/ats-scanner", pc.dim)));
  p(headerLine());
  p();

  return lines;
}

function generateRecommendations(result: MatchResult): string[] {
  const recs: string[] = [];
  const { score, missing_by_category: missing, sections, keyword_density: density, keyword_placement } = result;
  const dynamicMissing = result.dynamic_missing;
  const yoeReqs = result.yoe_requirements;
  const resumeYoe = result.resume_yoe;

  if (score < 50) {
    recs.push(
      `${pc.bold(pc.red("Critical:"))} Your resume matches only ${score.toFixed(0)}% of this JD. Focus on adding the top missing keywords from each category below.`,
    );
  }

  for (const req of yoeReqs) {
    const skillStr = req.skill ? ` of ${req.skill}` : "";
    if (!resumeYoe.has_dates) {
      recs.push(
        `${pc.bold(pc.yellow("Experience Dates:"))} The JD requires ${req.years}+ years${skillStr}. Add clear date ranges (e.g., 'Jan 2020 - Present') to your experience entries so ATS can verify tenure.`,
      );
      break;
    } else if (resumeYoe.total_years < req.years) {
      recs.push(
        `${pc.bold(pc.yellow("Experience Gap:"))} The JD requires ${req.years}+ years${skillStr}, but your resume shows ~${resumeYoe.total_years} years. Consider including freelance work, internships, or relevant academic projects to bridge the gap.`,
      );
    }
  }

  for (const cat of ["languages", "frameworks", "databases", "devops_cloud"]) {
    if (missing[cat]?.length) {
      const kws = missing[cat].slice(0, 3).join(", ");
      const catName = CAT_DISPLAY[cat]?.[1] ?? cat;
      recs.push(
        `${pc.bold(pc.yellow(`${catName}:`))} Missing ${kws}. ${
          !sections.skills
            ? "Add to your Skills section AND mention in Experience bullets for maximum ATS weight."
            : "Add these to your Skills section explicitly."
        }`,
      );
    }
  }

  if (!sections.summary) {
    recs.push(
      `${pc.bold(pc.blue("Add a Summary:"))} A professional summary lets you front-load 4-6 core keywords from the JD. ATS systems weight summary keywords highly.`,
    );
  }

  if (!sections.skills) {
    recs.push(
      `${pc.bold(pc.blue("Add a Skills Section:"))} A dedicated Skills section gets a 1.5x weight multiplier in most ATS systems. List your technical skills explicitly.`,
    );
  }

  if (!sections.projects && score < 75) {
    recs.push(
      `${pc.bold(pc.blue("Add Projects:"))} A Projects section lets you demonstrate skills with context. 'Built X using Python and React' scores higher than just listing them.`,
    );
  }

  const skillsKws = new Set(keyword_placement.skills ?? []);
  const expKws = new Set(keyword_placement.experience ?? []);
  const onlyInSkills = [...skillsKws].filter((k) => !expKws.has(k));
  if (onlyInSkills.length > 2) {
    const kws = onlyInSkills.slice(0, 3).join(", ");
    recs.push(
      `${pc.bold(pc.cyan("Prove Your Skills:"))} ${kws} appear only in your Skills list. Mention them in Experience bullets too — ATS rewards the 'Claim + Proof' pattern (skill listed AND demonstrated).`,
    );
  }

  if (density.status === "danger") {
    recs.push(
      `${pc.bold(pc.red("Keyword Stuffing Alert:"))} Your keyword density is ${density.density_pct}% (optimal: 3-8%). Modern ATS systems penalize over-repetition. Remove duplicate mentions.`,
    );
  } else if (density.stuffed_keywords.length) {
    const stuffed = density.stuffed_keywords
      .slice(0, 3)
      .map((s) => s.keyword)
      .join(", ");
    recs.push(
      `${pc.bold(pc.yellow("Repetition Warning:"))} ${stuffed} appear more than 4 times. BM25 scoring saturates after 3-4 mentions — extra repetitions add zero value.`,
    );
  }

  if (dynamicMissing.length > 2) {
    const kws = dynamicMissing.slice(0, 3).join(", ");
    recs.push(
      `${pc.bold(pc.yellow("JD-Specific Terms:"))} The JD mentions ${kws} which aren't standard taxonomy keywords. If you have experience with these, add them to your resume.`,
    );
  }

  if (score >= 85) {
    recs.push(
      `${pc.bold(pc.green("Excellent Match:"))} Strong alignment! Focus your cover letter on the 1-2 remaining gaps. Your resume should pass most ATS filters.`,
    );
  } else if (score >= 75) {
    recs.push(
      `${pc.bold(pc.green("Good Match:"))} Solid foundation. Address the missing keywords above and you'll be in the top tier of applicants for ATS scoring.`,
    );
  }

  if (!recs.length) {
    recs.push(
      `${pc.bold(pc.green("Well Optimized:"))} Your resume is well-aligned with this JD. Focus on quantifying achievements in your bullet points.`,
    );
  }

  return recs;
}

export function saveReport(
  result: MatchResult,
  outputPath: string,
  resumeName: string,
  jdName: string,
): void {
  const { writeFileSync } = require("node:fs") as typeof import("node:fs");
  const { extname } = require("node:path") as typeof import("node:path");

  const report = {
    generated_at: new Date().toISOString(),
    resume: resumeName,
    job_description: jdName,
    score: result.score,
    grade: result.grade,
    matched_count: result.matched_count,
    missing_count: result.missing_count,
    matched_by_category: result.matched_by_category,
    missing_by_category: result.missing_by_category,
    missing_phrases: result.missing_phrases,
    bonus_skills: result.bonus_skills,
    sections: result.sections,
  };

  const ext = extname(outputPath).toLowerCase();
  if (ext === ".json") {
    writeFileSync(outputPath, JSON.stringify(report, null, 2), "utf-8");
  } else {
    let text = `ATS Scanner Report\n`;
    text += `Generated: ${report.generated_at}\n`;
    text += `Score: ${result.score}% (Grade ${result.grade})\n\n`;
    text += `Matched Keywords (${result.matched_count}):\n`;
    for (const [cat, kws] of Object.entries(result.matched_by_category)) {
      text += `  ${cat}: ${kws.join(", ")}\n`;
    }
    text += `\nMissing Keywords (${result.missing_count}):\n`;
    for (const [cat, kws] of Object.entries(result.missing_by_category)) {
      text += `  ${cat}: ${kws.join(", ")}\n`;
    }
    writeFileSync(outputPath, text, "utf-8");
  }

  console.log(`\n  ${pc.green("✓")} Report saved to ${pc.white(outputPath)}\n`);
}
