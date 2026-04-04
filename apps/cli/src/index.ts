import { basename } from "node:path";
import { existsSync } from "node:fs";
import pc from "picocolors";
import { cleanText, computeMatch } from "@ats-scanner/core";
import { parseArgs, getInputInteractive } from "./cli.js";
import { extractText } from "./extractor.js";
import { printReport, saveReport, setColorEnabled } from "./reporter.js";
import { DEMO_RESUME, DEMO_JD } from "./demo.js";

const BANNER = String.raw`
   _  _____ ____   ____
  / \|_   _/ ___| / ___|  ___  __ _ _ __  _ __   ___ _ __
 / _ \ | | \___ \| |  _ / __|/ _\` | '_ \| '_ \ / _ \ '__|
/ ___ \| |  ___) | |_| |\__ \ (_| | | | | | | |  __/ |
/_/   \_\_| |____/ \____||___/\__,_|_| |_|_| |_|\___|_|
`;

async function main(): Promise<number> {
  const args = parseArgs();

  if (args.noColor) {
    setColorEnabled(false);
  }

  if (!args.scoreOnly) {
    if (process.stdout.isTTY) console.log(pc.cyan(BANNER));
    console.log(pc.dim("  Resume vs Job Description ATS Keyword Analyzer"));
    console.log(pc.dim("  github.com/Calebe94/ats-scanner\n"));
  }

  if (args.demo) {
    console.log(pc.yellow("\n  Running demo analysis...\n"));
    const resumeClean = cleanText(DEMO_RESUME);
    const jdClean = cleanText(DEMO_JD);
    const result = computeMatch(resumeClean, jdClean, DEMO_RESUME, DEMO_JD);
    printReport(result, "demo_resume.txt", "demo_job_description.txt");
    return 0;
  }

  let resumeRaw: string;
  let resumeName: string;
  let jdRaw: string;
  let jdName: string;

  if (args.resume) {
    if (!existsSync(args.resume)) {
      console.error(pc.red(`\n  Error: File not found: ${args.resume}\n`));
      return 1;
    }
    try {
      resumeRaw = extractText(args.resume);
      resumeName = basename(args.resume);
    } catch (e) {
      console.error(pc.red(`\n  Error reading resume: ${(e as Error).message}\n`));
      return 1;
    }
  } else {
    if (args.scoreOnly) {
      console.error(pc.red("Error: --resume required with --score-only"));
      return 1;
    }
    resumeRaw = await getInputInteractive("Step 1 of 2 — Paste your resume text");
    resumeName = "pasted_resume";
  }

  if (args.jd) {
    if (!existsSync(args.jd)) {
      console.error(pc.red(`\n  Error: File not found: ${args.jd}\n`));
      return 1;
    }
    try {
      jdRaw = extractText(args.jd);
      jdName = basename(args.jd);
    } catch (e) {
      console.error(pc.red(`\n  Error reading job description: ${(e as Error).message}\n`));
      return 1;
    }
  } else {
    if (args.scoreOnly) {
      console.error(pc.red("Error: --jd required with --score-only"));
      return 1;
    }
    jdRaw = await getInputInteractive("Step 2 of 2 — Paste the job description");
    jdName = "pasted_jd";
  }

  if (!resumeRaw.trim()) {
    console.error(pc.red("\n  Error: Resume text is empty.\n"));
    return 1;
  }
  if (!jdRaw.trim()) {
    console.error(pc.red("\n  Error: Job description text is empty.\n"));
    return 1;
  }

  if (!args.scoreOnly) console.log(pc.dim("\n  Analyzing...\n"));

  const resumeClean = cleanText(resumeRaw);
  const jdClean = cleanText(jdRaw);
  const result = computeMatch(resumeClean, jdClean, resumeRaw, jdRaw);

  if (args.scoreOnly) {
    console.log(result.score.toFixed(1));
    return 0;
  }

  printReport(result, resumeName, jdName);

  if (args.output) {
    try {
      saveReport(result, args.output, resumeName, jdName);
    } catch (e) {
      console.warn(pc.yellow(`  Warning: Could not save report: ${(e as Error).message}`));
    }
  }

  return 0;
}

main().then((code) => process.exit(code));
