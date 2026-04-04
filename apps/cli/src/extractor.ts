import { readFileSync } from "node:fs";
import { extname } from "node:path";
import { createInflateRaw } from "node:zlib";
import { stripLatex } from "@ats-scanner/core";

export function extractText(source: string): string {
  const ext = extname(source).toLowerCase();
  switch (ext) {
    case ".pdf":
      return extractPdf(source);
    case ".txt":
      return extractTxt(source);
    case ".tex":
      return extractTex(source);
    case ".docx":
      return extractDocx(source);
    default:
      throw new Error(
        `Unsupported file type: ${ext}. Use .txt, .pdf, .tex, or .docx`,
      );
  }
}

function extractTxt(path: string): string {
  const encodings: BufferEncoding[] = ["utf-8", "latin1"];
  for (const enc of encodings) {
    try {
      return readFileSync(path, { encoding: enc }).trim();
    } catch {
      continue;
    }
  }
  throw new Error(`Could not decode file: ${path}`);
}

function extractPdf(path: string): string {
  const data = readFileSync(path);
  const raw = data.toString("latin1");
  const parts: string[] = [];

  const btPattern = /BT([\s\S]*?)ET/g;
  const tjPattern = /\(([^)]*)\)\s*T[Jj]/g;
  const tjArray = /\[([^\]]*)\]\s*TJ/g;
  const strInArray = /\(([^)]*)\)/g;

  let btMatch: RegExpExecArray | null;
  while ((btMatch = btPattern.exec(raw)) !== null) {
    const block = btMatch[1];

    let tjMatch: RegExpExecArray | null;
    const tjPat = new RegExp(tjPattern.source, tjPattern.flags);
    while ((tjMatch = tjPat.exec(block)) !== null) {
      parts.push(tjMatch[1]);
    }

    let arrMatch: RegExpExecArray | null;
    const arrPat = new RegExp(tjArray.source, tjArray.flags);
    while ((arrMatch = arrPat.exec(block)) !== null) {
      let sm: RegExpExecArray | null;
      const sPat = new RegExp(strInArray.source, strInArray.flags);
      while ((sm = sPat.exec(arrMatch[1])) !== null) {
        parts.push(sm[1]);
      }
    }
  }

  let text = parts.join(" ");
  text = text.replace(/\\n/g, "\n").replace(/\\r/g, "\n").replace(/\\t/g, " ");
  text = text.replace(/\\([0-7]{3})/g, (_, oct) =>
    String.fromCharCode(parseInt(oct, 8)),
  );
  text = text.replace(/\s+/g, " ").trim();

  if (text.length < 50) {
    throw new Error(
      "PDF text extraction yielded too little text. Try saving as .txt first.",
    );
  }

  return text;
}

function extractTex(path: string): string {
  const raw = extractTxt(path);
  return stripLatex(raw);
}

function extractDocx(path: string): string {
  const data = readFileSync(path);
  const bytes = new Uint8Array(data.buffer, data.byteOffset, data.byteLength);

  let eocdOffset = -1;
  for (
    let i = bytes.length - 22;
    i >= Math.max(0, bytes.length - 65557);
    i--
  ) {
    if (
      bytes[i] === 0x50 &&
      bytes[i + 1] === 0x4b &&
      bytes[i + 2] === 0x05 &&
      bytes[i + 3] === 0x06
    ) {
      eocdOffset = i;
      break;
    }
  }
  if (eocdOffset < 0) throw new Error("Not a valid ZIP/DOCX file");

  const view = new DataView(
    data.buffer,
    data.byteOffset,
    data.byteLength,
  );
  const cdOffset = view.getUint32(eocdOffset + 16, true);
  const cdSize = view.getUint32(eocdOffset + 12, true);

  let pos = cdOffset;
  let docEntry: {
    compMethod: number;
    compSize: number;
    localOffset: number;
  } | null = null;

  while (pos < cdOffset + cdSize) {
    if (view.getUint32(pos, true) !== 0x02014b50) break;
    const compMethod = view.getUint16(pos + 10, true);
    const compSize = view.getUint32(pos + 20, true);
    const nameLen = view.getUint16(pos + 28, true);
    const extraLen = view.getUint16(pos + 30, true);
    const commentLen = view.getUint16(pos + 32, true);
    const localOffset = view.getUint32(pos + 42, true);
    const name = new TextDecoder().decode(bytes.slice(pos + 46, pos + 46 + nameLen));

    if (name === "word/document.xml") {
      docEntry = { compMethod, compSize, localOffset };
      break;
    }
    pos += 46 + nameLen + extraLen + commentLen;
  }

  if (!docEntry) throw new Error("word/document.xml not found in .docx");

  const localNameLen = view.getUint16(docEntry.localOffset + 26, true);
  const localExtraLen = view.getUint16(docEntry.localOffset + 28, true);
  const dataStart = docEntry.localOffset + 30 + localNameLen + localExtraLen;
  const compData = bytes.slice(dataStart, dataStart + docEntry.compSize);

  let xmlText: string;
  if (docEntry.compMethod === 0) {
    xmlText = new TextDecoder().decode(compData);
  } else {
    const inflated = inflateRawSync(Buffer.from(compData));
    xmlText = new TextDecoder().decode(inflated);
  }

  const ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
  const paragraphs: string[] = [];

  const pRegex = new RegExp(
    `<[^>]*?:?p(?:\\s[^>]*)?>([\\s\\S]*?)<\\/[^>]*?:?p>`,
    "g",
  );
  const tRegex = new RegExp(
    `<[^>]*?:?t(?:\\s[^>]*)?>([\\s\\S]*?)<\\/[^>]*?:?t>`,
    "g",
  );

  let pMatch: RegExpExecArray | null;
  while ((pMatch = pRegex.exec(xmlText)) !== null) {
    const pContent = pMatch[1];
    const texts: string[] = [];
    let tMatch: RegExpExecArray | null;
    const tPat = new RegExp(tRegex.source, tRegex.flags);
    while ((tMatch = tPat.exec(pContent)) !== null) {
      texts.push(tMatch[1]);
    }
    if (texts.length) paragraphs.push(texts.join(""));
  }

  const result = paragraphs.join("\n").trim();
  if (result.length < 10) {
    throw new Error(
      "DOCX text extraction yielded too little text. Try saving as .txt first.",
    );
  }

  return result;
}

function inflateRawSync(data: Buffer): Buffer {
  const { inflateRawSync: inflate } = require("node:zlib") as typeof import("node:zlib");
  return inflate(data);
}
