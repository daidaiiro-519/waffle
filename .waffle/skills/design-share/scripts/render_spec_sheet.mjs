#!/usr/bin/env node
// render_spec_sheet.mjs — DESIGN.mdを機械的にスペックシートHTMLへ変換する
//
// @google/design.md の公式lintパイプライン（lint()）でDESIGN.mdを解析し、
// 解決済みトークン（DesignSystemState）からスウォッチ・タイプスケール・スケール・
// コンポーネント実物を生成する。値はすべてトークンから導出し、この場で発明しない
// （round-tripを閉じる）。本文プロセ（Overview/Layout等）はDESIGN.mdのMarkdownを
// 素朴なHTML変換にかけるだけで、内容を創作しない。
//
// 使い方: node render_spec_sheet.mjs <DESIGN.mdパス> <出力HTMLパス>
//
// 前提: このディレクトリで `npm install` 済みであること（package.json参照）。
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';
import { lint, contrastRatio } from '@google/design.md/linter';
import { marked } from 'marked';

// spec.md記載の正規サブトークン一覧（ランタイムexportが無いためここに固定）
const VALID_COMPONENT_SUB_TOKENS = ['backgroundColor', 'textColor', 'typography', 'rounded', 'padding', 'size', 'height', 'width'];

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const [, , designMdPath, outPath] = process.argv;
if (!designMdPath || !outPath) {
  console.error('usage: node render_spec_sheet.mjs <DESIGN.mdパス> <出力HTMLパス>');
  process.exit(1);
}

const md = readFileSync(designMdPath, 'utf8');
const report = lint(md);

console.error(`lint結果: errors=${report.summary.errors} warnings=${report.summary.warnings} infos=${report.summary.infos}`);
for (const f of report.findings) console.error(`  [${f.severity}] ${f.path ?? ''} ${f.message}`);
if (report.summary.errors > 0) {
  console.error('エラーがあるため生成を中止します。DESIGN.mdを修正してください。');
  process.exit(1);
}

const ds = report.designSystem;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---- Markdown→HTML変換は確立されたライブラリ（marked）に委ねる。自前実装しない ----
function mdToHtml(body) {
  return marked.parse(body.trim());
}

// ---- DESIGN.mdの本文セクションを見出し単位で切り出す（生の.mdから直接。トークンは使わない） ----
function extractSections(rawMd) {
  const body = rawMd.replace(/^---[\s\S]*?---\n/, ''); // フロントマター除去
  const parts = body.split(/^##\s+(.+)$/m).slice(1); // [heading, content, heading, content, ...]
  const sections = {};
  for (let i = 0; i < parts.length; i += 2) {
    sections[parts[i].trim()] = parts[i + 1] || '';
  }
  return sections;
}
const sections = extractSections(md);

// ---- typography内のfontFamily+fontWeightから、同梱フォント資産(FONT:マーカー)を推測して@font-faceを生成する ----
const FONTS_DIR = path.join(__dirname, '../assets/fonts');
function findFontAsset(family, weight) {
  const w = weight || 400;
  const candidates = [
    family.toLowerCase().replace(/\s+/g, ''),
    family.toLowerCase().replace(/\s+/g, '-'),
    family.toLowerCase().replace(/\s+(?=\d)/, '').replace(/\s+/g, '-'),
  ];
  for (const c of candidates) {
    const name = `${c}-${w}`;
    if (existsSync(path.join(FONTS_DIR, `${name}.woff2`))) return name;
  }
  return null;
}
function fontFaceBlock() {
  const seen = new Set();
  const lines = [];
  const missing = [];
  for (const [, t] of ds.typography) {
    if (!t.fontFamily) continue;
    const key = `${t.fontFamily}:${t.fontWeight || 400}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const asset = findFontAsset(t.fontFamily, t.fontWeight);
    if (asset) {
      lines.push(`  @font-face{font-family:'${t.fontFamily}';font-weight:${t.fontWeight || 400};src:url(FONT:${asset}) format('woff2');font-display:swap}`);
    } else {
      missing.push(key);
    }
  }
  return { css: lines.join('\n'), missing };
}
const { css: fontFaceCss, missing: missingFonts } = fontFaceBlock();
if (missingFonts.length) console.error(`警告: 同梱フォント資産が見つかりません（システムフォントにフォールバック）: ${missingFonts.join(', ')}`);

// ---- CSSトークン（:root）を生成する。名前空間はDESIGN.mdのトークン名をそのまま使う ----
function cssVarBlock() {
  const lines = [];
  for (const [name, c] of ds.colors) lines.push(`  --color-${name}: ${c.hex};`);
  for (const [name, t] of ds.typography) {
    if (t.fontFamily) lines.push(`  --font-${name}: '${t.fontFamily}';`);
    if (t.fontSize) lines.push(`  --text-${name}: ${t.fontSize.value}${t.fontSize.unit};`);
    if (t.fontWeight) lines.push(`  --weight-${name}: ${t.fontWeight};`);
    if (t.letterSpacing) lines.push(`  --tracking-${name}: ${t.letterSpacing.value}${t.letterSpacing.unit};`);
    if (t.lineHeight) lines.push(`  --leading-${name}: ${t.lineHeight.value}${t.lineHeight.unit || ''};`);
  }
  for (const [name, d] of ds.rounded) lines.push(`  --radius-${name}: ${d.value}${d.unit};`);
  for (const [name, d] of ds.spacing) lines.push(`  --space-${name}: ${d.value}${d.unit};`);
  return lines.join('\n');
}

// ---- Colorsスウォッチ（対neutralコントラストを実計算） ----
function renderSwatches() {
  const neutral = ds.colors.get('neutral');
  return [...ds.colors].map(([name, c]) => {
    let crBadge = '';
    if (neutral && name !== 'neutral') {
      const cr = contrastRatio(c, neutral).toFixed(2);
      const cls = Number(cr) >= 4.5 ? 'pass' : 'warn';
      crBadge = `<span class="cr ${cls}">対neutral ${cr}:1</span>`;
    }
    return `<div class="swatch"><div class="chip" style="background:${c.hex}"></div>
      <div class="meta"><div class="tok">${esc(name)}</div><div class="hex">${c.hex}</div>${crBadge}</div></div>`;
  }).join('\n');
}

// ---- Typography実物 ----
function renderTypography() {
  return [...ds.typography].map(([name, t]) => {
    const style = [
      t.fontFamily && `font-family:'${t.fontFamily}'`,
      t.fontWeight && `font-weight:${t.fontWeight}`,
      t.fontSize && `font-size:${t.fontSize.value}${t.fontSize.unit}`,
      t.letterSpacing && `letter-spacing:${t.letterSpacing.value}${t.letterSpacing.unit}`,
    ].filter(Boolean).join(';');
    const label = [
      name,
      t.fontFamily,
      t.fontWeight && `weight ${t.fontWeight}`,
      t.fontSize && `${t.fontSize.value}${t.fontSize.unit}`,
    ].filter(Boolean).join(' · ');
    return `<div class="typerow"><span class="lbl">${esc(label)}</span><span style="${esc(style)}">Aa ${esc(name)}サンプル</span></div>`;
  }).join('\n');
}

// ---- Scale（spacing/rounded） ----
function renderScale() {
  const sp = [...ds.spacing].map(([name, d]) =>
    `<div class="u"><div class="box" style="width:${d.value}${d.unit};height:24px"></div>spacing.${esc(name)} · ${d.value}${d.unit}</div>`);
  const rd = [...ds.rounded].map(([name, d]) =>
    `<div class="u"><div class="box" style="width:40px;height:40px;border-radius:${d.value}${d.unit}"></div>rounded.${esc(name)} · ${d.value}${d.unit}</div>`);
  return [...sp, ...rd].join('\n');
}

// ---- Components実物（正規のサブトークンのみ使用、不明サブトークン・未解決参照はgapとして明示） ----
function renderComponents() {
  const previews = [];
  const gaps = [];
  for (const [name, def] of ds.components) {
    const style = [];
    for (const [prop, val] of def.properties) {
      if (!VALID_COMPONENT_SUB_TOKENS.includes(prop)) {
        gaps.push(`不明なサブトークン: components.${name}.${prop}`);
        continue;
      }
      if (val && typeof val === 'object' && val.type === 'color') style.push(`${cssPropFor(prop, 'color')}:${val.hex}`);
      else if (val && typeof val === 'object' && val.type === 'dimension') style.push(`${cssPropFor(prop, 'dimension')}:${val.value}${val.unit}`);
      else if (val && typeof val === 'object' && val.type === 'typography') {
        if (val.fontFamily) style.push(`font-family:'${val.fontFamily}'`);
        if (val.fontWeight) style.push(`font-weight:${val.fontWeight}`);
        if (val.fontSize) style.push(`font-size:${val.fontSize.value}${val.fontSize.unit}`);
      }
    }
    if (def.unresolvedRefs?.length) gaps.push(`未解決の参照: components.${name} → ${def.unresolvedRefs.join(', ')}`);
    previews.push(`<div class="preview"><div class="cap">${esc(name)}</div><div class="row"><span style="${esc(style.join(';'))}">${esc(name)}のサンプル</span></div></div>`);
  }
  return { html: previews.join('\n'), gaps };
}
function cssPropFor(tokenProp, kind) {
  const map = { backgroundColor: 'background-color', textColor: 'color', rounded: 'border-radius', padding: 'padding', size: 'font-size', height: 'height', width: 'width' };
  return map[tokenProp] || tokenProp;
}

const { html: componentsHtml, gaps } = renderComponents();

const doDontLists = (() => {
  const raw = sections["Do's and Don'ts"] || '';
  const doItems = [...raw.matchAll(/^-\s*Do:\s*(.+)$/gm)].map((m) => `<li>${marked.parseInline(m[1])}</li>`).join('');
  const dontItems = [...raw.matchAll(/^-\s*Don't:\s*(.+)$/gm)].map((m) => `<li>${marked.parseInline(m[1])}</li>`).join('');
  return { doItems, dontItems };
})();

const gapsHtml = gaps.length
  ? `<p class="gap">lint / 生成時の不足: ${gaps.map(esc).join(' / ')}</p>`
  : '';

// ---- 正本テンプレート（template-design-spec-body.html）を読み込み、{{...}}プレースフォルダーを機械的に埋める ----
const specBodyTemplate = readFileSync(path.join(__dirname, '../references/templates/template-design-spec-body.html'), 'utf8');
const bodyHtml = specBodyTemplate
  .replaceAll('{{デザイン名}}', esc(ds.name || ''))
  .replaceAll('{{デザイン説明}}', esc(ds.description || '') + gapsHtml)
  .replaceAll('{{バージョン表記}}', 'draft · 機械生成')
  .replaceAll('{{カラースウォッチ群}}', renderSwatches())
  .replaceAll('{{タイポグラフィ見本群}}', renderTypography())
  .replaceAll('{{Elevation本文}}', sections['Elevation & Depth'] ? mdToHtml(sections['Elevation & Depth']) : '<p class="gap">未記載（DESIGN.mdに「## Elevation & Depth」セクションが無い）</p>')
  .replaceAll('{{Shapes本文}}', sections['Shapes'] ? mdToHtml(sections['Shapes']) : '<p class="gap">未記載（DESIGN.mdに「## Shapes」セクションが無い）</p>')
  .replaceAll('{{スケール見本}}', renderScale())
  .replaceAll('{{コンポーネント見本群}}', componentsHtml)
  .replaceAll('{{Overview本文}}', mdToHtml(sections['Overview'] || ''))
  .replaceAll('{{Layout本文}}', mdToHtml(sections['Layout'] || ''))
  .replaceAll('{{Doリスト}}', doDontLists.doItems)
  .replaceAll('{{Dontリスト}}', doDontLists.dontItems);

const template = readFileSync(path.join(__dirname, '../references/templates/template-pattern-page.html'), 'utf8');
const out = template
  .replaceAll('{{パターン名}}', esc(ds.name || 'DESIGN.md スペックシート'))
  .replace(/:root\s*\{\s*\/\* \{\{デザイントークンCSS\}\}[^}]*\*\/\s*\}/, `${fontFaceCss}\n  :root {\n${cssVarBlock()}\n  }`)
  .replace('  <!-- {{モック本体}} — Design.mdのトークンとfrontend-design-principlesに基づいて生成する -->', bodyHtml);

writeFileSync(outPath, out, 'utf8');
console.error(`書き出しました: ${outPath}`);
