# Safe Corpus Grounding Audit

## Scope

This audit covers the current Milestone 8A implementation pass for the uploaded AegisQA working folder.

The folder `aegis-sensitive-data/` was treated as quarantined input only. It was not added to clean packaging and agents do not consume it directly at runtime.

## Raw input state

Quarantined input folders detected:

```text
aegis-sensitive-data/custom_libs  42 files
aegis-sensitive-data/robot        5 files
aegis-sensitive-data/output       1 file
aegis-sensitive-data/success      3 files
aegis-sensitive-data/fail         0 files
aegis-sensitive-data/LLD          0 files
```

Initial scanner result on the quarantined input detected potentially sensitive patterns, so the input was **not considered share-ready as-is**.

Detected pattern classes included:

```text
URLs
IP addresses
local paths
long identifiers
sensitive assignments
hostnames
```

No raw sensitive values are listed in this audit report.

## Sanitization result

The sanitizer produced:

```text
fixtures/reference_corpus/raw_sanitized/
```

Sanitization summary:

```text
Files sanitized: 51
Redactions applied: 7024
Custom library/reference files: 42
Robot test files: 5
Report examples: 1
Successful execution artifacts: 3
Failed execution artifacts: 0
LLD examples: 0
```

## Normalization result

The normalized corpus generator produced:

```text
fixtures/reference_corpus/normalized/robot_keywords/keyword_registry.json
fixtures/reference_corpus/normalized/robot_style_profile/profile.json
fixtures/reference_corpus/normalized/report_profile/profile.json
fixtures/reference_corpus/normalized/execution_evidence_profile/profile.json
fixtures/reference_corpus/normalized/NORMALIZATION_SUMMARY.json
```

Normalization summary:

```text
Robot keywords extracted: 238
Robot style files analyzed: 5
Report files analyzed: 1
Execution artifacts analyzed: 3
```

## Runtime consumption rule

Agents and tools consume only:

```text
fixtures/reference_corpus/normalized/*
```

They do not read:

```text
aegis-sensitive-data/*
```

## Agent/tool changes

Implemented changes:

- Added reference-corpus profile loaders.
- Added normalized corpus generation script.
- Extended Robot keyword registry with optional sanitized corpus capabilities.
- Updated Robot keyword tool to expose sanitized corpus capabilities.
- Updated automation generation to use sanitized Robot style profile metadata.
- Updated telecom automation generation to filter keyword calls against approved/corpus-aware registry.
- Updated Robot validation to reject unknown generated keywords unless they are BuiltIn or approved/corpus-backed.
- Updated investigation to add execution-evidence-profile context.
- Updated reporting to use report profile guidance after execution/investigation context exists.
- Updated clean packaging to exclude quarantined/raw sensitive inputs.

## Clean packaging result

The final clean package excludes:

```text
.env
lld.docx
.git
.venv
.tools
node_modules
dist
generated
data
aegis-sensitive-data
__pycache__
*.pyc
```

The clean package keeps sanitized reference-corpus files and normalized profiles.

## Verification

```bash
python -m pytest -q
# 148 passed

python -m compileall -q backend scripts tests
# passed

cd frontend
npm ci
npm run build
# build successful
```

## Remaining gap

The failed execution input folder currently contains no files. Once a sanitized failed execution example is available, rerun:

```bash
python scripts/sanitize_sensitive_data_repo.py --clean
python scripts/generate_reference_corpus_profiles.py
python -m pytest -q
```
