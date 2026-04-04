export function cleanText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s+#./]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function stripLatex(text: string): string {
  text = text.replace(/(?<!\\)%.*/g, "");
  text = text.replace(/\\(?:begin|end)\{[^}]*\}/g, "");
  text = text.replace(
    /\\(?:documentclass|usepackage|input|include|bibliography|bibliographystyle)(?:\[[^\]]*\])?\{[^}]*\}/g,
    "",
  );
  text = text.replace(/\\item\s*/g, "\n");

  const fmtRe =
    /\\(?:textbf|textit|emph|underline|texttt|textrm|textsf|textsc|section|subsection|subsubsection|paragraph|subparagraph|title|author|date)\*?\{([^}]*)\}/g;
  for (let i = 0; i < 3; i++) {
    const next = text.replace(fmtRe, "$1");
    if (next === text) break;
    text = next;
  }

  text = text.replace(/\\href\{[^}]*\}\{([^}]*)\}/g, "$1");
  text = text.replace(
    /\\(?:cvitem|cventry|cvlistitem|cvdoubleitem|cvcolumn|cvskill|cvitemwithcomment|name|address|email|phone|social|extrainfo)(?:\[[^\]]*\])?/g,
    " ",
  );
  text = text.replace(/\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})*/g, "");
  text = text.replace(/\\[\\&%$#_{}~^]/g, " ");
  text = text.replace(/[{}]/g, " ");
  text = text.replace(/[ \t]+/g, " ");
  text = text.replace(/\n\s*\n+/g, "\n");

  return text.trim();
}
