# nicepkg/deskmakeover (high_topic)

Old ADR: `docs/decisions/0001-tech-stack-and-support-baseline.md`
New ADR: `docs/decisions/0019-tauri-rust-replatform.md`
New ADR date: 2026-07-10T19:48:10+08:00
Partial: no

## Old ADR status line

** superseded by [ADR-0019](0019-tauri-rust-replatform.md) — the .NET 10 / WPF stack

## New ADR

ADR-0019 — Full replatform to Tauri 2 + Rust; .NET exits the product

- **Status**: Accepted (owner, 2026-07-10) - **Inputs**: 4-seat adversarial architecture panel (chief architect, chief Windows platform engineer, chief algorithms engineer — isolated seats — plus Codex/gpt-5.6 as cross-vendor chief architecture engineer, 2 adversarial rounds), the ChatGPT consultation `docs/references/gpt-refactor-suggest.md`, and repo evidence cited below. - **Supersedes**: ADR-0001 (the .NET/WPF half of the tech stack), ADR-0011 (WPF+WebView2 host). **Amends**: ADR-0014 (wallp

## Best commit

`1609e1f5463b2264016607f09ed557601ee9bece` (after)

build: scaffold cargo workspace for the Tauri+Rust replatform (ADR-0019 M0)

commit title names ADR 19; commit title matches the new ADR: replatform, tauri, rust; changes application code

Changed files:

- M .gitignore
- A Cargo.lock
- A Cargo.toml
- A crates/dm-contracts/Cargo.toml
- A crates/dm-contracts/src/lib.rs
- A crates/dm-domain/Cargo.toml
- A crates/dm-domain/src/lib.rs
- A crates/dm-icon-codec/Cargo.toml
- A crates/dm-icon-codec/src/lib.rs
- A crates/dm-icon-core/Cargo.toml
- A crates/dm-icon-core/src/lib.rs
- A crates/dm-icon-wasm/Cargo.toml
- A crates/dm-icon-wasm/src/lib.rs
- A crates/dm-operations/Cargo.toml
- A crates/dm-operations/src/lib.rs
- A crates/dm-resident/Cargo.toml
- A crates/dm-resident/src/lib.rs
- A crates/dm-test-support/Cargo.toml
- A crates/dm-test-support/src/lib.rs
- A crates/dm-windows/Cargo.toml
- A crates/dm-windows/src/lib.rs
- A deny.toml
- A rust-toolchain.toml

## Other candidates

8a125d9d4f6f docs: Tauri 2 + Rust replatform decided (ADR-0019/0020/0021, spec 07, M0-M8 plan; 2b9a6184cca6 docs(specs): reconcile specs to the Tauri/Rust + schema-8 reality (ADR-0019); f93c7c1aa7a6 docs: de-stale the onboarding docs to the Tauri/Rust reality (ADR-0019); 147c876e2550 feat(bridge): route wallpaper verbs to Rust under Tauri (A7); 49da02f5816c docs(reviews): full Rust workspace + bridge audit — 12-slice codex carpet review; 7c33ccaa38bb feat: full product shell - title bar, settings drawer, about page, toast, declut; 871c7f1e946a docs(development): finish the Tauri/Rust de-stale the first pass missed; 7247b9a57761 docs(replatform): M6 perf architecture + wave-2 Windows hardening triage (26 Cod
