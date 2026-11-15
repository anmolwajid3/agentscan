# refactoringhq/tolaria (high_cooccur)

Old ADR: `docs/adr/0049-per-note-icon-property.md`
New ADR: `docs/adr/0174-lazy-full-phosphor-icon-catalog.md`
New ADR date: 2026-08-06T19:08:56+02:00
Partial: no

## Old ADR status line

active

## New ADR

Context

ADR-0049 made Phosphor names part of the durable `_icon` value contract and noted that a substantially larger registry should move away from eager loading. The original registry hand-selected 287 icons. Enumerating the package root exposes all 1,530 unique public icon names, but also makes every SVG component reachable from the startup chunk. In the measured production build that grew the main App chunk from about 3.87 MB to 7.78 MB and its gzip size from about 1.04 MB to 1.83 MB. Rendering all 

## Best commit

`4860b5b2f127713a61a68875c22d36de21de4557` (before)

refactor: share context menu positioning

removes or replaces something named in the old ADR; changes application code

Changed files:

- R082 src/components/note-list/contextMenuPosition.ts src/components/contextMenuPosition.ts
- A src/components/folder-tree/FolderContextMenu.test.tsx
- M src/components/folder-tree/FolderContextMenu.tsx
- M src/components/note-list/NoteListChangesMenuView.tsx
- M src/components/note-list/NoteListContextMenuView.tsx

## Other candidates

9ba862fdda79 chore: remove accidentally committed demo-vault and scripts from tracking; 05c686311980 feat: add Rename section to sidebar context menu; 1694676472eb feat: wikilink pills in message bubbles, noteList context injection; 2137de8bac7a feat: seed AGENTS.md in Getting Started vault and expose via vault_context MCP t; 2a615358a38e feat: add contextual native editor formatting menus; 36cf694b13cf refactor: split ai workspace context helpers; 37009248d160 refactor: split changes context menu helpers; 3744a25929a4 fix: open folder context menu for mounted vault folders (#1256)
