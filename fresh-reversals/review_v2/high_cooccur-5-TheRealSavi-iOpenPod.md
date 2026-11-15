# TheRealSavi/iOpenPod (high_cooccur)

Old ADR: `docs/adr/0208-prepare-game-authorizations-with-a-standalone-codec.md`
New ADR: `docs/adr/0219-confirm-unverified-game-compatibility.md`
New ADR date: 2026-10-31T16:25:36-04:00
Partial: no

## Old ADR status line

ADR-0219 supersedes this admission requirement with explicit confirmation for

## New ADR

ADR-0219: Confirm unverified game compatibility

- Status: Accepted - Date: 2026-10-31

## Best commit

`a3163e04ef8741623ae3cd87a126d05952f5dc67` (after)

Convert ID3 to v2.3 for compatibility with iPod

commit title matches the new ADR: compatibility; changes application code

Changed files:

- M CONTEXT.md
- M docs/adr/0206-validate-native-lyrics-publication.md
- M docs/research/lyrics-firmware-adoption.md
- M docs/source_architecture.md
- M src/iOpenPod/app/media/lyrics.py
- M tests/iOpenPod/app/services/test_hp_mini_identification.py
- M tests/iOpenPod/app/test_media_lyrics.py
- M tests/iOpenPod/app/test_sync_lyrics_replacement.py

## Other candidates

08fd51300a1d Empty state game UI; 121c2ca161c3 Podcasts unsubscrive confirms removal of eps; 3c97233e292f Thanks to Olsro for game preservation efforts; a452673cea4b Games; e923dde980ff Allowing trying games on unknown hardware identities; e9684f23e401 Add games info to readme and website; 005c178e9b61 Fix Genius test module name collision (#272); 01b98a5eb7c1 Fix Packaging
