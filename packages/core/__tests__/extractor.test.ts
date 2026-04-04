import { describe, it, expect } from "vitest";
import { cleanText, stripLatex } from "../src/index.js";

describe("TextExtraction", () => {
  it("lowercases text", () => {
    expect(cleanText("Hello WORLD Python")).toBe("hello world python");
  });

  it("removes special characters", () => {
    const result = cleanText("hello, world! test@email.com");
    expect(result).not.toContain(",");
    expect(result).not.toContain("!");
  });

  it("preserves tech tokens", () => {
    const result = cleanText("C++ and C# are languages");
    expect(result).toContain("c++");
    expect(result).toContain("c#");
  });
});

describe("TexExtraction", () => {
  it("preserves content from formatting", () => {
    const text = String.raw`\textbf{Python} and \emph{Java} developer`;
    const result = stripLatex(text);
    expect(result).toContain("Python");
    expect(result).toContain("Java");
    expect(result).toContain("developer");
    expect(result).not.toContain("\\textbf");
    expect(result).not.toContain("\\emph");
  });

  it("removes comments", () => {
    const text = "Python developer % this is a comment\nJava expert";
    const result = stripLatex(text);
    expect(result).toContain("Python");
    expect(result).toContain("Java");
    expect(result).not.toContain("comment");
  });

  it("handles href", () => {
    const text = String.raw`\href{https://github.com/user}{My GitHub Profile}`;
    const result = stripLatex(text);
    expect(result).toContain("My GitHub Profile");
    expect(result).not.toContain("https://");
  });

  it("handles sections", () => {
    const text = String.raw`\section{Experience}\subsection{Company A}`;
    const result = stripLatex(text);
    expect(result).toContain("Experience");
    expect(result).toContain("Company A");
  });

  it("removes preamble", () => {
    const text = String.raw`\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
Actual content here`;
    const result = stripLatex(text);
    expect(result).toContain("Actual content");
    expect(result).not.toContain("documentclass");
    expect(result).not.toContain("geometry");
  });

  it("handles escaped chars", () => {
    const text = String.raw`R\&D department, 100\% effort`;
    const result = stripLatex(text);
    expect(result).toContain("R");
    expect(result).toContain("D department");
  });

  it("handles nested commands", () => {
    const text = String.raw`\textbf{\emph{Python}} and \textit{\texttt{Java}} developer`;
    const result = stripLatex(text);
    expect(result).toContain("Python");
    expect(result).toContain("Java");
    expect(result).toContain("developer");
    expect(result).not.toContain("\\textbf");
    expect(result).not.toContain("\\emph");
    expect(result).not.toContain("{");
  });
});
