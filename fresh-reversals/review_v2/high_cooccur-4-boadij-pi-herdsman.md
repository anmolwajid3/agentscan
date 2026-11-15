# boadij/pi-herdsman (high_cooccur)

Old ADR: `docs/adr/0025-propagate-explicit-required-assignment-evidence.md`
New ADR: `docs/adr/0028-reference-historical-assignment-evidence.md`
New ADR date: 2026-10-21T11:49:24+02:00
Partial: no

## Old ADR status line

Accepted

## New ADR

Reference historical assignment evidence

Accepted

## Best commit

`31b2e2ca5649a950693d2eecea4d76dfb2654890` (after)

fix(evidence): expose retained refs in initial Lead assignments (#968)

commit title matches the new ADR: assignment, evidence; changes application code

Changed files:

- M SKILL.md
- M docs/guides/handoffs.md
- M extension/agent-controller.ts
- M extension/controller-api.test.ts
- M extension/extension-contract.test.ts
- M extension/lead/project.ts

## Other candidates

50e9f815f22f feat(evidence): deliver historical requirements through semantic refs (#493); 717d24343da1 feat(evidence): inherit managed Agent work assignments (#672); 8749f8263e43 fix(evidence): name generated assignment notes as Markdown (#472); c6e6de170b7b feat(coordination): propagate required assignment evidence (#450); 2b78e1b7b4a6 refactor!: clarify project and work assignment semantics (#657); 01f9b2713835 fix(manager): align project assignment payload limits (#217); 0ba2d9c7d043 feat(manager): support evidence handoffs in resume_work (#810); 1a7c90d66cf9 test(smoke): own Herdr bootstrap and preserve failure evidence (#394)
