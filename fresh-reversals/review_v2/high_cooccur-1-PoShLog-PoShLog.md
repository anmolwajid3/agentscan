# PoShLog/PoShLog (high_cooccur)

Old ADR: `docs/decisions/0010-v2-maintenance-line.md`
New ADR: `docs/decisions/0033-net10-powershell-7-6.md`
New ADR date: 2026-11-04T18:58:50+01:00
Partial: no

## Old ADR status line

- **Note (2026-11-04):** v3 now requires PowerShell 7.6 ([0033](0033-net10-powershell-7-6.md), superseding 0001).

## New ADR

— v3 targets net10.0 and PowerShell 7.6+

- **Status:** accepted (Tomáš, 2026-11-04) - **Date:** 2026-11-04 - **Supersedes:** [0001](0001-binary-module-net8-powershell-7-4.md)

## Best commit

`080d8e38e76ecac6086ba94338aa364d71a7317c` (same)

Move v3 to net10.0 and PowerShell 7.6+ (ADR 0033 supersedes 0001)

commit title names ADR 33; commit title matches the new ADR: net10.0, powershell; changes application code

Changed files:

- M .github/workflows/ci.yml
- M .github/workflows/compat.yml
- M .github/workflows/integration.yml
- M .github/workflows/recipes.yml
- M .github/workflows/release.yml
- M CHANGELOG.md
- M README.md
- M build/Build-Extension.ps1
- M build/Invoke-IntegrationTests.ps1
- M build/Test-ExtensionInstall.ps1
- M build/Test-PackageInstall.ps1
- M build/Test-Recipes.ps1
- M docs/assets/banner-dark.svg
- M docs/assets/banner-light.svg
- M docs/assets/quick-start-console.svg
- M docs/compatibility.md
- M docs/decisions/0001-binary-module-net8-powershell-7-4.md
- M docs/decisions/0010-v2-maintenance-line.md
- M docs/decisions/0030-mssqlserver-private-dependencies.md
- A docs/decisions/0033-net10-powershell-7-6.md
- M docs/decisions/README.md
- M docs/getting-started.md
- M docs/guides/creating-sink.md
- M docs/guides/extension-modules.md
- M docs/guides/faq.md

## Other candidates

4922407116ea Fix file sink paths relative to the PowerShell location (#41); 55323762d06d Destructure PowerShell objects the way PowerShell shows them (#46); 7d8e9f9c09ca Rewrite PoShLog as a compiled C# binary PowerShell module; 4034431c4c4e Install PowerShell 7.4 to an absolute path in the minimum-PowerShell CI job; af41f509f000 Verify issue features in fresh PowerShell hosts and record release evidence; d08b0b91f540 Add PowerShell Gallery publishing workflows; ffd48b054549 Merge senior-dev/psobj-ergonomics: PowerShell object ergonomics (#46, #48, #34, ; 05d173bc53ac Add Get-PoShLogExtension and Install-PoShLogExtension (ADR 0021)
