#!/usr/bin/env node
/**
 * Validate repository hygiene, HTML/CSS/JS snippet quality, JSON/CSV integrity,
 * and script syntax across Frontend Library.
 *
 *   node scripts/check-code.mjs
 */
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { extname, join, dirname, resolve } from "node:path";
import vm from "node:vm";

const ROOT = resolve(".");
const errors = [];

const FORBIDDEN_DIRS = new Set(["node_modules", "dist", "build", "out", ".idea"]);
const FORBIDDEN_FILES = new Set([".DS_Store", "Thumbs.db", ".env", ".env.local"]);
const KEBAB_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SECRET_PATTERNS = [
  { name: "Private key block", re: new RegExp("-----BEGIN [A-Z ]*PRIVATE " + "KEY-----") },
  { name: "GitHub classic token", re: new RegExp("\\b" + "gh" + "[pousr]_[A-Za-z0-9]{20,}\\b") },
  { name: "GitHub fine-grained token", re: new RegExp("\\bgithub_" + "pat_[A-Za-z0-9_]{20,}\\b") },
  { name: "AWS access key", re: new RegExp("\\bAK" + "IA[0-9A-Z]{16}\\b") },
];
const TEXT_EXTS = new Set([".html", ".css", ".js", ".mjs", ".py", ".json", ".yml", ".yaml", ".md", ".csv"]);

function fail(msg) {
  errors.push(msg);
}

function walk(dir, files = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === ".git") continue;
    const full = join(dir, entry.name);
    const rel = full.slice(ROOT.length + 1);

    if (entry.isDirectory()) {
      if (FORBIDDEN_DIRS.has(entry.name)) {
        fail(`Forbidden directory committed: ${rel}`);
        continue;
      }
      walk(full, files);
      continue;
    }

    if (
      FORBIDDEN_FILES.has(entry.name) ||
      entry.name.startsWith(".env.") ||
      entry.name.endsWith(".swp") ||
      entry.name.endsWith(".swo")
    ) {
      fail(`Forbidden file committed: ${rel}`);
      continue;
    }
    files.push({ full, rel, ext: extname(entry.name).toLowerCase() });
  }
  return files;
}

function checkSnippetDirs(baseRel) {
  const dir = join(ROOT, baseRel);
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name === "_shared") continue;
    const rel = `${baseRel}/${entry.name}`;
    if (!KEBAB_RE.test(entry.name)) {
      fail(`Folder name must be lowercase kebab-case: ${rel}`);
    }
    if (!existsSync(join(dir, entry.name, "index.html"))) {
      fail(`Missing index.html inside asset directory: ${rel}`);
    }
  }
}

function scanHtmlSections(html) {
  const lower = html.toLowerCase();
  const markupParts = [];
  const styles = [];
  const scripts = [];
  let cursor = 0;

  while (cursor < html.length) {
    const nextScript = lower.indexOf("<script", cursor);
    const nextStyle = lower.indexOf("<style", cursor);
    let next = -1;
    let tag = "";
    if (nextScript !== -1 && (nextStyle === -1 || nextScript < nextStyle)) {
      next = nextScript;
      tag = "script";
    } else if (nextStyle !== -1) {
      next = nextStyle;
      tag = "style";
    }
    if (next === -1) {
      markupParts.push(html.slice(cursor));
      break;
    }
    const afterTag = lower[next + 1 + tag.length];
    if (afterTag && !/[\s>/]/.test(afterTag)) {
      markupParts.push(html.slice(cursor, next + 1 + tag.length));
      cursor = next + 1 + tag.length;
      continue;
    }
    markupParts.push(html.slice(cursor, next));
    const openEnd = html.indexOf(">", next);
    if (openEnd === -1) break;
    const attrs = html.slice(next + 1 + tag.length, openEnd);
    const closeStart = lower.indexOf(`</${tag}`, openEnd + 1);
    if (closeStart === -1) {
      cursor = openEnd + 1;
      break;
    }
    const closeEnd = html.indexOf(">", closeStart);
    const content = html.slice(openEnd + 1, closeStart);
    if (tag === "script") scripts.push({ attrs, content });
    else styles.push(content);
    cursor = closeEnd === -1 ? closeStart + tag.length + 3 : closeEnd + 1;
  }

  return { markupOnly: markupParts.join(""), styles, scripts };
}

function checkHtml(full, rel, text) {
  const lower = text.toLowerCase();
  if (!lower.includes("<!doctype html>")) fail(`${rel}: missing <!doctype html>`);
  if (!/<html\b[^>]*\blang\s*=/i.test(text)) fail(`${rel}: <html> tag must declare a lang attribute`);
  if (!/<meta\b[^>]*\bcharset\b/i.test(text)) fail(`${rel}: missing <meta charset>`);
  if (!/<meta\b[^>]*\bname\s*=\s*["']viewport["']/i.test(text)) fail(`${rel}: missing viewport meta tag`);
  if (!/<title>[^<]+<\/title>/i.test(text)) fail(`${rel}: missing non-empty <title>`);

  const { markupOnly, styles, scripts } = scanHtmlSections(text);

  const imgTags = markupOnly.match(/<img\b[^>]*>/gi) || [];
  for (const img of imgTags) {
    if (!/\balt\s*=/i.test(img)) {
      fail(`${rel}: <img> missing alt attribute: ${img}`);
    }
  }

  // Verify local relative href/src references outside <script>/<style> resolve in the repo.
  const refRe = /\b(?:href|src)\s*=\s*["']([^"']+)["']/gi;
  let refMatch;
  while ((refMatch = refRe.exec(markupOnly)) !== null) {
    const ref = refMatch[1].trim();
    if (!ref || /^(?:https?:|data:|mailto:|#|javascript:)/i.test(ref)) continue;
    const cleanRef = ref.split(/[?#]/)[0];
    if (!cleanRef) continue;
    const target = resolve(dirname(full), cleanRef);
    if (!existsSync(target)) {
      fail(`${rel}: broken local asset reference '${ref}'`);
    }
  }

  // Enforce reduced-motion media query when styles animate or transition elements.
  const styleBlocks = styles.join("\n");
  if (/(?:@keyframes|animation\s*:|transition\s*:)/i.test(styleBlocks) && !/prefers-reduced-motion/i.test(text)) {
    fail(`${rel}: uses CSS animation/transition without @media (prefers-reduced-motion: reduce)`);
  }

  // Validate syntax & safety of inline scripts.
  let idx = 0;
  for (const { attrs, content } of scripts) {
    idx += 1;
    if (/\bsrc\s*=/i.test(attrs)) continue;
    const typeMatch = attrs.match(/\btype\s*=\s*["']([^"']+)["']/i);
    if (typeMatch && !/^(?:text\/javascript|application\/javascript|module)$/i.test(typeMatch[1].trim())) {
      continue;
    }
    const code = content.trim();
    if (!code) continue;
    if (!typeMatch || typeMatch[1].trim().toLowerCase() !== "module") {
      try {
        new vm.Script(code, { filename: `${rel}#script-${idx}` });
      } catch (err) {
        fail(`${rel} (script #${idx}): JavaScript syntax error — ${err.message}`);
      }
    }
    if (/\b(?:eval|document\.write)\s*\(|new\s+Function\s*\(/.test(code)) {
      fail(`${rel} (script #${idx}): disallowed dynamic execution API (eval / Function / document.write)`);
    }
  }
}

function checkCsv(rel, text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) {
    fail(`${rel}: CSV appears empty`);
    return;
  }
  const header = lines[0].split(",");
  if (header.length !== 5) {
    fail(`${rel}: expected 5 header columns, found ${header.length}`);
  }
}

function main() {
  const files = walk(ROOT);
  checkSnippetDirs("animations/snippets");
  checkSnippetDirs("components");

  for (const { full, rel, ext } of files) {
    if (!TEXT_EXTS.has(ext)) continue;
    const text = readFileSync(full, "utf8");

    for (const { name, re } of SECRET_PATTERNS) {
      if (re.test(text)) {
        fail(`${rel}: potential secret detected (${name})`);
      }
    }

    if (ext === ".json") {
      try {
        JSON.parse(text);
      } catch (err) {
        fail(`${rel}: invalid JSON — ${err.message}`);
      }
    } else if (ext === ".html") {
      checkHtml(full, rel, text);
    } else if (ext === ".js" || ext === ".mjs") {
      try {
        execFileSync(process.execPath, ["--check", full], { stdio: "pipe" });
      } catch (err) {
        fail(`${rel}: JS syntax check failed — ${err.stderr?.toString().trim() || err.message}`);
      }
      if (rel !== "scripts/check-code.mjs" && /\b(?:eval|document\.write)\s*\(|new\s+Function\s*\(/.test(text)) {
        fail(`${rel}: disallowed dynamic execution API (eval / Function / document.write)`);
      }
    } else if (rel === "data/sources.csv") {
      checkCsv(rel, text);
    }
  }

  if (errors.length) {
    console.error(`Code checks failed with ${errors.length} issue(s):`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`ok: checked ${files.length} files across repository (HTML/CSS/JS, JSON, CSV, naming & hygiene)`);
}

main();
