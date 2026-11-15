# ghuntley/overalls (high_topic)

Old ADR: `docs/architecture/decisions/0114-overalls-workspace-design.md`
New ADR: `docs/architecture/decisions/0119-authenticated-control-room-reads.md`
New ADR date: 2026-10-17T09:48:21+00:00
Partial: no

## Old ADR status line

- Superseded by: ADR-0116, ADR-0119, ADR-0161

## New ADR

ADR-0119: Authenticated read access to the Control room

- ID: ADR-0119 - Date: 2026-09-25 - Status: superseded - Implementation: implemented - Components: Marshall Accounts, authorization, web, compute, fleet, SSH, access - Supersedes: ADR-0059, ADR-0062, ADR-0065, ADR-0114 - Superseded by: ADR-0123

## Best commit

`0f617141c15244a1cb99329bd671879ca376281a` (after)

android: bind authenticated notification device controls

commit title matches the new ADR: authenticated, control; changes application code

Changed files:

- M mila/native/PARITY_MATRIX.md
- M mila/native/android/app/src/main/java/dev/overalls/mila/nativeui/MilaFfiAdapter.kt
- M mila/native/android/app/src/main/java/dev/overalls/mila/nativeui/MilaNotifications.kt
- M mila/native/linux/src/session.rs
- M mila/native/linux/src/terminal.rs
- M mila/rust/mila-ffi/src/lib.rs

## Other candidates

26322c1a271c lilly: reverify empty checkpoint outputs without root read access; 2a6564957b4d feat(web): hide account and reference navigation in the Control room; 352a7ded7f10 windows: add authenticated notification device controls; 3b7976e539ed android: bind authenticated web controls; 4d25076e4aed linux: add authenticated SSH key listing control; 4dbd6fd19e6a test(scim): follow control room auth redirects; 611928cd2de8 linux: add authenticated notification device controls; 8de96d57fbf2 Complete Windows authenticated web settings control
