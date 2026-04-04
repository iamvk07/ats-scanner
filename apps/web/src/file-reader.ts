import { stripLatex } from "@ats-scanner/core";

export async function readFile(
  file: File,
): Promise<{ text: string; warning: string | null }> {
  const name = file.name.toLowerCase();

  if (name.endsWith(".pdf")) return readPdf(file);
  if (name.endsWith(".tex")) return readTex(file);
  if (name.endsWith(".docx")) return readDocx(file);
  return readTxt(file);
}

function readTxt(file: File): Promise<{ text: string; warning: string | null }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = () => resolve({ text: reader.result as string, warning: null });
    reader.onerror = () => reject(new Error("Could not read file"));
  });
}

function readPdf(file: File): Promise<{ text: string; warning: string | null }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsBinaryString(file);
    reader.onload = () => {
      const raw = reader.result as string;
      const parts: string[] = [];
      const blocks = raw.match(/BT[\s\S]*?ET/g) ?? [];
      for (const b of blocks) {
        const matches = b.match(/\(([^)]*)\)\s*T[Jj]/g) ?? [];
        for (const s of matches) {
          const m = s.match(/\(([^)]*)\)/);
          if (m) parts.push(m[1].replace(/\\n/g, "\n").replace(/\\\d{3}/g, ""));
        }
      }
      const text =
        parts.join(" ").replace(/\s+/g, " ").trim() ||
        raw.replace(/[^\x20-\x7E\n]/g, " ").trim();
      const warning = text.length < 100 ? "limited extraction — try .txt" : null;
      resolve({ text, warning });
    };
    reader.onerror = () => reject(new Error("Could not read PDF"));
  });
}

function readTex(file: File): Promise<{ text: string; warning: string | null }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsText(file);
    reader.onload = () => {
      resolve({ text: stripLatex(reader.result as string), warning: null });
    };
    reader.onerror = () => reject(new Error("Could not read .tex file"));
  });
}

async function readDocx(file: File): Promise<{ text: string; warning: string | null }> {
  const buffer = await file.arrayBuffer();

  if (typeof DecompressionStream === "undefined") {
    throw new Error("Your browser does not support .docx reading — please paste text instead");
  }

  const bytes = new Uint8Array(buffer);
  let eocdOffset = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
    if (bytes[i] === 0x50 && bytes[i + 1] === 0x4b && bytes[i + 2] === 0x05 && bytes[i + 3] === 0x06) {
      eocdOffset = i;
      break;
    }
  }
  if (eocdOffset < 0) throw new Error("Not a valid ZIP file");

  const view = new DataView(buffer);
  const cdOffset = view.getUint32(eocdOffset + 16, true);
  const cdSize = view.getUint32(eocdOffset + 12, true);

  let pos = cdOffset;
  let docEntry: { compMethod: number; compSize: number; localOffset: number } | null = null;
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
    const ds = new DecompressionStream("deflate-raw");
    const writer = ds.writable.getWriter();
    writer.write(compData);
    writer.close();
    const reader = ds.readable.getReader();
    const chunks: Uint8Array[] = [];
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }
    const total = chunks.reduce((s, c) => s + c.length, 0);
    const result = new Uint8Array(total);
    let off = 0;
    for (const c of chunks) {
      result.set(c, off);
      off += c.length;
    }
    xmlText = new TextDecoder().decode(result);
  }

  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlText, "application/xml");
  const ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
  const paragraphs: string[] = [];
  for (const p of doc.getElementsByTagNameNS(ns, "p")) {
    const texts: string[] = [];
    for (const t of p.getElementsByTagNameNS(ns, "t")) {
      if (t.textContent) texts.push(t.textContent);
    }
    if (texts.length) paragraphs.push(texts.join(""));
  }
  return { text: paragraphs.join("\n").trim(), warning: null };
}
