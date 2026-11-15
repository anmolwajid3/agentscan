# CaliCastle/cali.so (high_topic)

Old ADR: `docs/adr/0009-clerk-owner-metadata.md`
New ADR: `docs/adr/0012-owner-admin-without-step-up.md`
New ADR date: 2026-07-19T00:15:30+08:00
Partial: no

## Old ADR status line

Accepted. This supersedes ADR-0004 and the immutable-user-ID allowlist direction previously recorded in issue #93. ADR-0011 supersedes the provider capability switch requirement, and ADR-0012 supersedes the step-up verification requirement below. Clerk is the sole runtime authentication system for o

## New ADR

Keep owner admin behind one authoritative Clerk boundary

Accepted. This supersedes the step-up verification requirement in ADR-0009.

## Best commit

`93e399a28ec90318f831b727c6c2dbe83415e3a1` (before)

fix: keep owner admin available

commit title matches the new ADR: keep, owner, admin; removes or replaces something named in the old ADR; changes application code

Changed files:

- M .env.example
- M .github/workflows/security.yml
- M README.md
- M app/admin/(protected)/layout.tsx
- M app/admin/(protected)/page.tsx
- M app/admin/layout.tsx
- M app/admin/login/page.tsx
- M app/api/admin/ama/availability/route.ts
- M app/api/admin/ama/google/callback/route.ts
- M app/api/admin/ama/google/connect/route.ts
- M app/api/admin/ama/google/disconnect/route.ts
- M app/api/admin/auth/logout/route.ts
- M app/api/admin/auth/request/route.ts
- M app/api/admin/auth/verify/route.ts
- M docs/adr/0003-retire-comments-reactions-guestbook.md
- M docs/adr/0004-magic-link-admin-auth-replaces-clerk.md
- A docs/adr/0008-owner-admin-is-always-available.md
- M docs/handoff.md
- M docs/security/baseline.md
- M docs/security/verification.md
- M docs/v3-cutover-readiness.md
- M e2e/instant-navigation.spec.ts
- M lib/ama/admin/http.test.ts
- M lib/ama/admin/http.ts
- D lib/ama/admin/launch-boundary-server.ts

## Other candidates

ebb8e5be77f0 fix: authorize admin with Clerk; f801ee1b9f0f feat(admin): redesign the owner admin around the public design language (#171); 6ae4164db47b fix(admin): keep Clerk session token fresh in the background; a00fc4d51785 fix(admin): allow Clerk origins in the admin CSP; a9fead091389 fix(admin): provide Clerk session context; ad71a09aca68 feat: harden Clerk owner reverification; de410e45f7b8 refactor: separate admin analytics boundary; fee2a4a4554a docs(admin): cite the verified Clerk version for the static provider
