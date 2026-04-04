import { Command } from "commander";
import { createInterface } from "node:readline/promises";
import { stdin, stdout } from "node:process";

export interface CliOptions {
  resume?: string;
  jd?: string;
  output?: string;
  scoreOnly: boolean;
  noColor: boolean;
  demo: boolean;
}

export function parseArgs(argv?: string[]): CliOptions {
  const program = new Command();

  program
    .name("ats-scanner")
    .description(
      "ATS Scanner — Analyze how well your resume matches a job description.\n\n" +
        "Supports .txt, .pdf, .tex, and .docx files, or paste text directly.\n\n" +
        "Examples:\n" +
        "  ats-scanner --resume resume.txt --jd job.txt\n" +
        "  ats-scanner --resume resume.pdf --jd job.txt --output report.json\n" +
        "  ats-scanner --resume resume.txt --jd job.txt --score-only",
    )
    .version("1.0.0", "-v, --version")
    .option("-r, --resume <path>", "Path to your resume (.txt, .pdf, .tex, or .docx)")
    .option("-j, --jd <path>", "Path to job description (.txt, .pdf, .tex, or .docx)")
    .option("-o, --output <path>", "Save report to file (.txt or .json)")
    .option("-s, --score-only", "Print only the score number", false)
    .option("--no-color", "Disable colored output")
    .option("--demo", "Run with built-in demo data", false);

  program.parse(argv ?? process.argv);
  const opts = program.opts();

  return {
    resume: opts.resume,
    jd: opts.jd,
    output: opts.output,
    scoreOnly: opts.scoreOnly ?? false,
    noColor: !opts.color,
    demo: opts.demo ?? false,
  };
}

export async function getInputInteractive(label: string): Promise<string> {
  const rl = createInterface({ input: stdin, output: stdout });
  console.log(`\n  ${label}`);
  console.log("  Paste text below. Enter a blank line when done:");
  console.log("  " + "─".repeat(50));

  const lines: string[] = [];
  try {
    while (true) {
      const line = await rl.question("  ");
      if (line === "" && lines.length > 0 && lines[lines.length - 1] === "") {
        break;
      }
      lines.push(line);
    }
  } finally {
    rl.close();
  }
  return lines.join("\n").trim();
}
