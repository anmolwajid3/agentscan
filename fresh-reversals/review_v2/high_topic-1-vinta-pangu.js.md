# vinta/pangu.js (high_topic)

Old ADR: `docs/adr/0019-plus-after-a-word-reads-as-a-separator.md`
New ADR: `docs/adr/0024-name-suffixes-belong-to-core-spacing.md`
New ADR date: 2026-09-10T14:46:41+08:00
Partial: no

## Old ADR status line

**Partially superseded by [ADR 0024](0024-name-suffixes-belong-to-core-spacing.md): core owns the accepted list and produces the suffix outputs in every consumer.

## New ADR

Name suffixes belong to core spacing

Move the existing name-suffix list into core. Its outputs belong to every pangu consumer: `Disney+上架` becomes `Disney+ 上架`, and `血型是AB-的人` becomes `血型是 AB- 的人`. The AI toggle controls model-dependent corrections only. Keeping the list in the extension with a separate toggle filter would preserve a package difference we no longer want.

## Best commit

`899c5a707f91b6bd7d2fc32a73a06949d8a9ef9d` (same)

fix: move name suffix corrections into core

commit title matches the new ADR: name, core; removes or replaces something named in the old ADR; changes application code

Changed files:

- M CONTEXT.md
- M browser-extensions/chrome/src/ai-spacing/content-script.ts
- M browser-extensions/chrome/src/ai-spacing/shapes/base.ts
- D browser-extensions/chrome/src/ai-spacing/shapes/name-suffix-shape.ts
- M docs/adr/0013-protected-word-list-removed.md
- M docs/adr/0018-cjk-brand-suffixes-return-as-an-extension-late-fix.md
- M docs/adr/0019-plus-after-a-word-reads-as-a-separator.md
- M docs/adr/0022-plus-after-a-closing-bracket-reads-as-a-separator.md
- A docs/adr/0024-name-suffixes-belong-to-core-spacing.md
- M src/browser/dom/boundary-spacing.ts
- M src/browser/pangu.ts
- M src/shared/index.ts
- A src/shared/name-suffix.ts
- M tests/browser/pangu.playwright.ts
- M tests/extension/ai-spacing.test.ts
- M tests/extension/hyphen-sign.test.ts
- D tests/extension/name-suffix.test.ts
- A tests/shared/name-suffix.test.ts
- M tests/shared/symbol-plus-sign.test.ts

## Other candidates

9588a5b6266e refactor: merge name suffix rules into shared core; 15d7aaea8a4f refactor: handle name suffixes in core rules; 119d7ddbf335 refactor: align AI spacing names with domain types; 58df623d138d refactor: name queued node spacing callback explicitly; 1582ab4cbd18 feat: add Letterlike Symbols to ANS sets, join TM/SM to superscript suffixes; 40e8866c7dc9 fix: keep Unicode superscript suffixes attached; 75c997d57e2a refactor: remove protected word list, CJK brand suffixes read as operators; 98f05ef8bec0 fix: read bundle-plan pluses as separators, not brand suffixes
