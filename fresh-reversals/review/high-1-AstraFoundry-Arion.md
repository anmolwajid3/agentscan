# AstraFoundry/Arion (high)

Old ADR: `docs/decisions/013-rewrite-context-on-device.md`
New ADR: `docs/decisions/012-context-scene-selection.md`

## Old ADR status line

Accepted (product decision). [ADR 024](024-shared-polishing-pipeline.md) supersedes the on-device-only transport restriction: enabled context may reach the explicitly selected cloud polishing provider. Amends the consent rule of [009](../../specs/009-contextual-rewrite.md) step 2 and PRV-02 of [005]

## New ADR

ADR 012: Scene selection from the focused field, site and app

Accepted (product decision). Extends [ADR 011](011-live-local-rewriting.md). Scene selection remains; prompt `live-v2` is superseded by [ADR 018](018-staged-gguf-rewriting.md).

## Commits

### a5c73fc2543e7aca36e0827182097a2edf96fdd7 (same)

feat(rewrite): switch rewrite scenes by focused field, site and app

Each dictation decides its scene locally from metadata: a scene the user
chose for the place, then a search field, then the host of the focused web
page, then the app's bundle ID, else chat. The prompt stays live-v2:
scenes map onto its chat, email and list layouts, and search queries get
deterministic finishing. A live-v3 prompt teaching the new scenes lowered
the held-out live set from 27 to 22 and was rejected.

The menu bar panel shows a card with the current field's scene; choosing
another one stores it for that site or app on this device. Match the app
in Settings turns scene selection off.

Adds the scene classifier benchmark, SCENE/CORRECT modes for the text
bench, ADR 012, spec SCN-01..05 and the scene-switching-

Changed files:

- Makefile
- apps/desktop/bootstrap/actions.go
- apps/desktop/bootstrap/app.go
- apps/desktop/bootstrap/platform.go
- apps/desktop/bootstrap/platform_darwin.go
- apps/desktop/bootstrap/platform_windows.go
- apps/desktop/bootstrap/scene.go
- apps/desktop/bootstrap/windows.go
- apps/desktop/cmd/arion-rewrite-bench/main.go
- apps/desktop/cmd/arion-scene-bench/main.go
- apps/desktop/e2e/native_test.go
- apps/desktop/e2e/site_darwin_test.go
- apps/desktop/infrastructure/llm/prompt/prompt.go
- apps/desktop/infrastructure/llm/prompt/prompt_test.go
- apps/desktop/infrastructure/macos/macos.go
- apps/desktop/infrastructure/macos/native.h
- apps/desktop/infrastructure/macos/native.m
- apps/desktop/infrastructure/settings/settings_test.go
- apps/desktop/infrastructure/windows/windows.go
- apps/desktop/ui/app/app_test.go
- apps/desktop/ui/app/polish_test.go
- apps/desktop/ui/app/scene_test.go
- apps/desktop/ui/features/polish/polish.go
- apps/desktop/ui/features/scene/scene.go
- apps/desktop/ui/pages/menubar/menubar.go
- apps/desktop/ui/pages/settings/settings.go
- apps/desktop/ui/shared/copy/copy.go
- apps/desktop/ui/shared/copy/locales/en.json
- apps/desktop/ui/shared/copy/locales/zh-CN.json
- apps/desktop/ui/shared/icons/icons.go
- apps/desktop/ui/shared/icons/svg/briefcase.svg
- apps/desktop/ui/shared/icons/svg/chevrons-up-down.svg
- apps/desktop/ui/shared/icons/svg/code.svg
- apps/desktop/ui/shared/icons/svg/mail.svg
- apps/desktop/ui/shared/icons/svg/message-circle.svg
- apps/desktop/ui/shared/icons/svg/search.svg
- apps/desktop/ui/shared/runtime/runtime.go
- benchmarks/README.md
- benchmarks/configs/scene-contexts.json
- benchmarks/configs/scene-switching-report.json

### 206de2dfeb5aacd40acfbb1cd3455a57ef3b4243 (after)

feat(site): show github authors on blog posts and the index (#55)

Changed files:

- apps/site/package.json

### f39a4b3e7a918d86ecca50f2cb1eb03c4b8f7b15 (after)

refactor(repo): separate public product from private evaluation

Changed files:

- benchmarks/migration/README.md
- benchmarks/migration/archive.json
- benchmarks/migration/clean-check.json
- benchmarks/migration/import-plan.json
- benchmarks/migration/inventory.json
- benchmarks/migration/verification.json
- benchmarks/reproduction/context-memory-v1/workflow-source/package.json
- benchmarks/reproduction/evaluation-source/tools/evaluation/package.json
- benchmarks/reproduction/llm-ime-alignment-v1/source/apps/desktop/go.mod
- benchmarks/reproduction/native-asr-v1/source-driver/apps/desktop/go.mod
- benchmarks/reproduction/native-asr-v1/source-driver/apps/desktop/infrastructure/settings/asr_migration_test.go
- benchmarks/reproduction/native-asr-v1/source-driver/models/go.mod
- benchmarks/reproduction/native-asr-v1/source-driver/packages/core/go.mod
- benchmarks/reproduction/qwen17-accessibility-v1/source-final/apps/desktop/go.mod
- benchmarks/reproduction/qwen17-accessibility-v1/source/apps/desktop/go.mod
- benchmarks/reproduction/qwen17-accessibility-v1/workflow-source/package.json
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/packages/core/go.mod

### 17a1a7026b38dffa3c70e167118ba7fb5602ccdf (after)

fix(security): upgrade the site to next 16.4.3

Changed files:

- apps/site/package.json

### 99fa8d82c63f23a7f67fc9b4b848e7d7953b4127 (after)

feat(site): add a blog with markdown posts, embeds and lazy media

Changed files:

- apps/site/package.json

### f3374fdf70ae092d637f391c6d4ff5f5fd62c811 (after)

feat(rewriting): preserve recognized names across final rewrite

Changed files:

- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-prior/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-development-no-screen/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline-2/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-intent-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/final-v5/runs/final-validation-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-prior/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-prior/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-prior/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-screen/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-screen/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/development-no-screen/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-baseline/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-baseline/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-baseline/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-candidate/sources/apps/desktop/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-candidate/sources/models/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/native-pairs-candidate/sources/packages/core/go.mod
- benchmarks/reproduction/rewrite-stage-preservation-v1/evidence/rejected-v1/matrix-1/validation-baseline/sources/apps/desktop/go.mod

### 5db000478c10e83b6dea49f26cbbbd70caf28e6a (after)

feat(site): offer downloads from the arion center

Changed files:

- apps/site/src/shared/config/env-schema.ts

### 2ca6a3f0ecdeec37b4c16307503c3ee2acc9a102 (after)

feat(benchmarks): archive the staged rewrite studies

Changed files:

- benchmarks/runs/rewrite-entity-evidence-v1/source-snapshot/apps/desktop/go.mod
- benchmarks/runs/rewrite-product-integration-v1/sources/apps/desktop/go.mod
- benchmarks/runs/rewrite-product-integration-v1/sources/models/go.mod
- benchmarks/runs/rewrite-product-integration-v1/sources/packages/core/go.mod
- benchmarks/runs/rewrite-selector-model-v1/failed-schema/case-outcomes.jsonl
- benchmarks/runs/rewrite-selector-model-v1/failed-schema/manifest.json
- benchmarks/runs/rewrite-selector-model-v1/failed-schema/results.jsonl
- benchmarks/runs/rewrite-selector-model-v1/failed-schema/selector-model-v1-baseline-work-props.json
- benchmarks/runs/rewrite-selector-model-v1/failed-schema/selector-model-v1-baseline-work-server.log
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/failure.json
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/freeze.json.txt
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/host-provenance.json
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/pipeline.py.txt
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/protocol.json.txt
- benchmarks/runs/rewrite-selector-sentence-choice-v1/preflight-schema-projection/test_payload.py.txt

### 237f9f74a53287a7c237afd5dd8a19a0b195d8f2 (after)

fix(dictation): preserve ocr context and correction word boundaries

Changed files:

- benchmarks/reproduction/context-memory-v1/workflow-source/package.json
- benchmarks/reproduction/user-modify-asr-v3/workflow-source/package.json
- package.json

### dd5399385b4342043d4bddc71ec712d3fd01c38f (after)

fix(site): write the brand as astrafoundry in copy, docs and comments

Changed files:

- apps/site/src/shared/config/env-schema.ts

### 2da6070dce6b7295b7993ff654dffcc3fb75e6bc (after)

feat(site): scaffold the static next.js site with vendored sunbeam and beui

Changed files:

- apps/site/package.json
- apps/site/src/shared/config/env-schema.ts

### 28296c9e6ad0f7f5ede7d4d22071bd1024a3147c (after)

feat(rewrite): read cursor, screen and history context on device

Polishing can now read three context sources, each with its own switch,
on by default while polishing is on (ADR 013): text around the cursor
through Accessibility, the focused window's text recognized by the OS
(macOS ScreenCaptureKit + Vision; Windows PrintWindow + Windows.Media.Ocr,
compile-checked only) and the last dictations inserted in the same place,
kept in memory. Secure fields and password managers are never read; the
window image is never stored and nothing leaves the device.

Context reaches the model as spellings extracted into the prompt's terms;
the whole context is validation evidence, and proposals that copy context
or let it stand in for the dictation are rejected. The engine also serves
a context-section 

Changed files:

- Makefile
- apps/desktop/bootstrap/actions.go
- apps/desktop/bootstrap/app.go
- apps/desktop/bootstrap/platform.go
- apps/desktop/bootstrap/platform_darwin.go
- apps/desktop/bootstrap/platform_windows.go
- apps/desktop/cmd/arion-llm/main.go
- apps/desktop/cmd/arion-ocr/main.go
- apps/desktop/cmd/arion-rewrite-bench/main.go
- apps/desktop/e2e/context_darwin_test.go
- apps/desktop/e2e/windows_insert_test.go
- apps/desktop/infrastructure/llm/client/client.go
- apps/desktop/infrastructure/llm/engine/engine.go
- apps/desktop/infrastructure/llm/engine/parity_test.go
- apps/desktop/infrastructure/llm/prompt/context.json
- apps/desktop/infrastructure/llm/prompt/prompt.go
- apps/desktop/infrastructure/llm/protocol/protocol.go
- apps/desktop/infrastructure/macos/context.go
- apps/desktop/infrastructure/macos/context.h
- apps/desktop/infrastructure/macos/context.m
- apps/desktop/infrastructure/macos/macos.go
- apps/desktop/infrastructure/windows/ocr.go
- apps/desktop/infrastructure/windows/windows.go
- apps/desktop/ui/app/app_test.go
- apps/desktop/ui/app/polish_test.go
- apps/desktop/ui/app/scene_test.go
- apps/desktop/ui/features/polish/polish.go
- apps/desktop/ui/features/scene/scene.go
- apps/desktop/ui/pages/settings/settings.go
- apps/desktop/ui/shared/copy/copy.go
- apps/desktop/ui/shared/copy/locales/en.json
- apps/desktop/ui/shared/copy/locales/zh-CN.json
- apps/desktop/ui/shared/runtime/runtime.go
- benchmarks/README.md
- benchmarks/configs/context-ablation-report.json
- benchmarks/results/context-ablation-v1/README.md
- benchmarks/results/context-ablation-v1/ocr.json
- benchmarks/results/context-ablation-v1/summary.json
- docs/decisions/013-rewrite-context-on-device.md
- docs/decisions/README.md
