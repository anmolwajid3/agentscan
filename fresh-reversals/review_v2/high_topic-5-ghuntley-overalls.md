# ghuntley/overalls (high_topic)

Old ADR: `docs/architecture/decisions/0125-fresh-guest-identities.md`
New ADR: `docs/architecture/decisions/0158-durable-guest-identities.md`
New ADR date: 2026-10-17T09:48:21+00:00
Partial: no

## Old ADR status line

- Superseded by: ADR-0158

## New ADR

ADR-0158: Durable guest identities independent of email

- ID: ADR-0158 - Date: 2026-10-10 - Status: superseded - Implementation: partial - Components: Marshall Accounts, SSH, terminal, Editor, Lyra, NixOS, Ubuntu, Arch and Alma guests - Supersedes: ADR-0125, ADR-0148, ADR-0153 - Superseded by: ADR-0159

## Best commit

`cdb7a23c233ec5debce3dff9ec290d7c8488b527` (after)

Make HLDD source and chapter reviews independently mergeable

commit title matches the new ADR: independent; changes application code; changes configuration or schema named in the ADR: durable, guest, identities, email, guest, identities

Changed files:

- M .agents/skills/hldd-maintenance/SKILL.md
- M AGENTS.md
- M devenv.nix
- M docs/README.md
- M docs/architecture/README.md
- M docs/architecture/decisions/0122-hldd-section-pages.md
- M docs/architecture/decisions/0158-durable-guest-identities.md
- A docs/architecture/decisions/0250-independent-hldd-review-records.md
- M docs/architecture/decisions/README.md
- M docs/architecture/reviews/2026-09-26-guest-trust-evidence.md
- M docs/architecture/reviews/2026-10-10-durable-guest-identities.md
- M docs/architecture/reviews/2026-10-13-antithesis-reset.md
- A docs/architecture/reviews/2026-10-20-hldd-independent-reviews.md
- M docs/architecture/reviews/README.md
- D docs/hldd-maintenance.json
- A docs/hldd/README.md
- A docs/hldd/groups/deployment.yaml
- A docs/hldd/groups/governance.yaml
- A docs/hldd/groups/lilly.yaml
- A docs/hldd/groups/marshall.yaml
- A docs/hldd/groups/mila.yaml
- A docs/hldd/groups/protocol.yaml
- A docs/hldd/groups/services.yaml
- A docs/hldd/groups/system.yaml
- A docs/hldd/reviews/chapters/01-system.md

## Other candidates

1101dd9ef2f5 fix(scim): refuse deactivated identities on every live-account check; 2462fdc8724f Keep suspension fixture independent of private edge; 5ac1b6adebdf linux: add GTK-independent deployment, terminal, SSH-key and link models; 88682c113a14 test: capture native process identities on launch failure; 8b8bea13ca36 fix(scim): finalize retired identities; b2c504fec6fa test(github-fleet): enroll transfer identities for relocation; follow GitHub rev; db46c4acf8c8 test(enrico): bound the precommit suite by running independent real work concurr; 830185ac8b41 ci(mila): test Apple native package independently
