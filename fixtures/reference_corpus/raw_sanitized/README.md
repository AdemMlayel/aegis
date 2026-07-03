# Sanitized Aegis Data

This repo contains sanitized reference material only.
Raw sensitive files were not committed here.

## Layout

- `robot-tests/`: sanitized Robot test plans.
- `custom-libs/`: sanitized custom library references.
- `report-example/`: sanitized report artifact examples.
- `successful-execution/`: sanitized successful execution artifacts.
- `failed-execution/`: sanitized failed execution artifacts when available.
- `ticket-examples/`: sanitized structured or semi-structured test tickets.
- `lld-examples/`: sanitized low-level-design examples when available.

## Safety

- Original filenames are replaced with generic names.
- Original paths are stored only as non-reversible hashes.
- URLs, IP addresses, tokens, credential values, long identifiers, and local paths are replaced with placeholders.
- Binary media from spreadsheets is not copied.

## Manifest

`SANITIZATION_MANIFEST.json` contains counts, target paths, source path hashes, and redaction totals.

## Summary

- Files sanitized: `61`
- Redactions applied: `15073`
