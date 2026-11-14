# itgalaxy/webfont (low)

Old ADR: `docs/adr/0015-vitest-globals-in-workspaces.md`
New ADR: `docs/adr/0002-jest-vs-vitest-testing.md`

## Old ADR status line

After adopting Vitest ([ADR 0002](./0002-jest-vs-vitest-testing.md) superseded), `packages/webfont` already ran with `test

## New ADR

ADR 0002: Keep Jest instead of migrating to Vitest

- **Status:** Superseded (Vitest adopted, 2026-07-02) - **Date:** 2026-07-02

## Commits

### 47a34fbed00b2da3655038b6f84e5db29c087e5b (after)

build: emit declarations with TypeScript 7 tsc (#825)

Changed files:

- packages/webfont/vite.config.ts

### e1f62bf7db2efcb93db50571947abad917f2bfcf (after)

chore: npm workspaces monorepo and docs restructuring (#780)

Changed files:

- packages/webfont/vite.config.ts

### 4d8257adfcb9a180e6b2d2be3bd8a462c7dc8ff5 (after)

build(deps): host VitePress docs site on Vercel (#775)

Changed files:

- vite.config.ts

### a66dbb8e613e52eb03cb3648cdde8464f9275b0c (after)

build: enforce tsc typecheck over tests and harden test typings (#752)

Changed files:

- vite.config.ts

### 862247f59ae226fd4443f451be8a8d1486bff8e2 (after)

fix(build): expose callable default export from ESM build (#618) (#735)

Changed files:

- vite.config.ts

### 3e753070a298a42c31396a3bdf2aab8e201686f6 (after)

feat: svgTools diagnostics, ADR 0011, and browser entry stub (#198) (#715)

Changed files:

- vite.config.ts

### 2a1a98575c4123daacd5db1647ccf867f020b275 (after)

chore(deps): bump meow to 14.1.0 and ship CLI as dist/cli.mjs (#684)

Changed files:

- vite.config.ts

### e17e43e57a4d7c37949b9c9c01378e682be82987 (after)

build: add vite-plugin-dts and checker, drop tsc postbuild (#682)

Changed files:

- vite.config.ts

### a05a922d4a4eb68b80466fb53db1f8af3be0c4ef (after)

build: replace Rollup with Vite library mode for CLI and lib (#681)

Changed files:

- vite.config.ts
