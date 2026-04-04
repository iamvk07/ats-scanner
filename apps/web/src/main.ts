import "./style.css";
import { runAnalysis } from "./scanner.js";
import { renderResults } from "./ui.js";
import { readFile } from "./file-reader.js";

let resumeContent = "";
let jdContent = "";

function $(id: string): HTMLElement {
  return document.getElementById(id)!;
}

function switchTab(which: string, mode: string, btn: HTMLElement): void {
  const pre = which === "resume" ? "resume" : "jd";
  $(`${pre}-paste`).style.display = mode === "paste" ? "" : "none";
  $(`${pre}-upload`).style.display = mode === "upload" ? "" : "none";
  btn.closest(".tab-pair")!.querySelectorAll<HTMLElement>(".tp-btn").forEach((b) => b.classList.remove("on"));
  btn.classList.add("on");
  $(`${pre}Card`).classList.toggle("upload-mode", mode === "upload");
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

function getFileExt(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : "txt";
}

function truncatePreview(text: string, maxLines: number): string {
  const lines = text.split("\n").slice(0, maxLines);
  const preview = lines.join("\n");
  const totalLines = text.split("\n").length;
  if (totalLines > maxLines) return preview + "\n… (" + (totalLines - maxLines) + " more lines)";
  return preview;
}

function showUploadLoading(which: string): void {
  const zone = $(which === "resume" ? "resumeDrop" : "jdDrop");
  zone.classList.add("loading");
  zone.classList.remove("has");
  $(`${which}FileInfo`).classList.remove("show");
}

function showFileInfo(which: string, file: File, text: string, warning: string | null): void {
  const zone = $(which === "resume" ? "resumeDrop" : "jdDrop");
  zone.classList.remove("loading");
  zone.style.display = "none";

  const ext = getFileExt(file.name);
  $(`${which}FiName`).textContent = file.name;
  $(`${which}FiBadge`).textContent = "." + ext;
  $(`${which}FiSize`).textContent = formatFileSize(file.size) + (warning ? " · " + warning : "");
  $(`${which}PreviewBody`).textContent = truncatePreview(text, 20);

  const preview = $(`${which}Preview`);
  preview.classList.remove("collapsed");
  preview.querySelector(".fi-preview-toggle")!.textContent = "Hide";
  $(`${which}FileInfo`).classList.add("show");
}

function showFileError(which: string, msg: string): void {
  const zone = $(which === "resume" ? "resumeDrop" : "jdDrop");
  zone.classList.remove("loading");
  zone.classList.add("has");
  const nameEl = $(`${which}FName`);
  nameEl.textContent = "✗ " + msg;
  (nameEl as HTMLElement).style.color = "var(--red)";
}

async function handleFile(which: string, input: HTMLInputElement): Promise<void> {
  const file = input.files?.[0];
  if (!file) return;
  showUploadLoading(which);

  try {
    const { text, warning } = await readFile(file);
    if (which === "resume") resumeContent = text;
    else jdContent = text;
    showFileInfo(which, file, text, warning);
  } catch {
    showFileError(which, "Could not read file — try pasting text instead");
  }
}

function changeFile(which: string, event: Event): void {
  event.stopPropagation();
  const zone = $(which === "resume" ? "resumeDrop" : "jdDrop");
  zone.style.display = "";
  zone.classList.remove("has", "loading");
  $(`${which}FileInfo`).classList.remove("show");
  $(`${which}FName`).textContent = "";
  ($(`${which}FName`) as HTMLElement).style.color = "";
  if (which === "resume") resumeContent = "";
  else jdContent = "";
  ($(`${which === "resume" ? "resume" : "jd"}File`) as HTMLInputElement).click();
}

function togglePreview(which: string, event: Event): void {
  event.stopPropagation();
  const preview = $(`${which}Preview`);
  const btn = preview.querySelector(".fi-preview-toggle") as HTMLElement;
  const collapsed = preview.classList.toggle("collapsed");
  btn.textContent = collapsed ? "Show" : "Hide";
}

function onDrag(event: DragEvent, over: boolean, id: string): void {
  event.preventDefault();
  $(id).classList.toggle("drag", over);
}

function onDrop(event: DragEvent, which: string): void {
  event.preventDefault();
  const zoneId = which === "resume" ? "resumeDrop" : "jdDrop";
  $(zoneId).classList.remove("drag");
  const file = event.dataTransfer?.files[0];
  if (!file) return;
  const dt = new DataTransfer();
  dt.items.add(file);
  const input = $(`${which === "resume" ? "resume" : "jd"}File`) as HTMLInputElement;
  input.files = dt.files;
  handleFile(which, input);
}

function cardClick(which: string, event: Event): void {
  const target = event.target as HTMLElement;
  if (target.closest(".tp-btn") || target.closest(".ic-tip") || target.closest("textarea") || target.closest(".upload-zone")) return;
  if (target.closest(".ic-head")) {
    ($(`${which === "resume" ? "resume" : "jd"}File`) as HTMLInputElement).click();
  }
}

function clearAll(): void {
  ($(  "resumeText") as HTMLTextAreaElement).value = "";
  ($("jdText") as HTMLTextAreaElement).value = "";
  $("results").style.display = "none";
  resumeContent = "";
  jdContent = "";
  ["resumeFName", "jdFName"].forEach((id) => {
    const el = $(id);
    el.textContent = "";
    (el as HTMLElement).style.color = "";
  });
  document.querySelectorAll<HTMLElement>(".upload-zone").forEach((z) => {
    z.classList.remove("has", "drag", "loading");
    z.style.display = "";
  });
  ["resume", "jd"].forEach((pre) => {
    $(`${pre}FileInfo`).classList.remove("show");
  });
  (document.getElementById("scoreRing") as unknown as SVGCircleElement).style.strokeDashoffset = "251";
  ["resume", "jd"].forEach((pre) => {
    $(`${pre}-paste`).style.display = "";
    $(`${pre}-upload`).style.display = "none";
    const pair = $(`${pre}Card`).querySelector(".tab-pair")!;
    pair.querySelectorAll<HTMLElement>(".tp-btn").forEach((b) => b.classList.remove("on"));
    (pair.querySelector(".tp-btn:first-child") as HTMLElement).classList.add("on");
    $(`${pre}Card`).classList.remove("upload-mode");
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function runScan(): void {
  const resume = $("resume-paste").style.display !== "none"
    ? ($("resumeText") as HTMLTextAreaElement).value.trim()
    : resumeContent;
  const jd = $("jd-paste").style.display !== "none"
    ? ($("jdText") as HTMLTextAreaElement).value.trim()
    : jdContent;

  if (!resume) { alert("Please paste or upload your resume first."); return; }
  if (!jd) { alert("Please paste or upload the job description first."); return; }

  const btn = $("scanBtn");
  btn.classList.add("loading");
  (btn as HTMLButtonElement).disabled = true;

  setTimeout(() => {
    const result = runAnalysis(resume, jd);
    btn.classList.remove("loading");
    (btn as HTMLButtonElement).disabled = false;
    renderResults(result);
  }, 350);
}

/* Wire up all global event handlers */
(window as Record<string, unknown>).switchTab = switchTab;
(window as Record<string, unknown>).handleFile = handleFile;
(window as Record<string, unknown>).cardClick = cardClick;
(window as Record<string, unknown>).runScan = runScan;
(window as Record<string, unknown>).clearAll = clearAll;
(window as Record<string, unknown>).onDrag = onDrag;
(window as Record<string, unknown>).onDrop = onDrop;
(window as Record<string, unknown>).changeFile = changeFile;
(window as Record<string, unknown>).togglePreview = togglePreview;
