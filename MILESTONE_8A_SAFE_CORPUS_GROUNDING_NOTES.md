# Milestone 8A — Safe Corpus Grounding Notes

## Goal

Use sanitized Robot, report and execution examples to ground AegisQA without exposing raw sensitive project files or connecting to company systems.

## Important boundary

`aegis-sensitive-data/` is treated as a quarantine input folder. It is not source code, not packaged, and not read directly by agents at runtime.

The safe pipeline is:

```text
aegis-sensitive-data/
  -> scripts/intake_reference_corpus.py
  -> sanitizer/redaction + safety scan
  -> fixtures/reference_corpus/raw_sanitized/
  -> normalized profiles
  -> agents/tools consume only normalized outputs
```

## Sanitization result

Current sanitized corpus result:

```text
Files sanitized: 61
Redactions applied: 15073
Robot test/support files: 14
Custom library/reference files: 42
Report examples: 0 currently provided
Successful execution artifacts: 3
Failed execution artifacts: 0 currently provided
Ticket/semi-structured input files: 2
LLD examples: 0 currently provided
```

The failed execution folder exists but currently has no files. When a sanitized failed execution example is available, it should be added and the pipeline should be rerun.

## Normalized outputs

Generated profiles:

```text
fixtures/reference_corpus/normalized/robot_keywords/keyword_registry.json
fixtures/reference_corpus/normalized/robot_style_profile/profile.json
fixtures/reference_corpus/normalized/report_profile/profile.json
fixtures/reference_corpus/normalized/execution_evidence_profile/profile.json
fixtures/reference_corpus/normalized/ticket_profile/profile.json
fixtures/reference_corpus/normalized/NORMALIZATION_SUMMARY.json
fixtures/reference_corpus/INTAKE_SUMMARY.json
```

Current normalized summary:

```text
Robot keywords extracted: 238
Robot style files analyzed: 12
Report examples analyzed: 0
Execution artifacts analyzed: 3
Ticket files analyzed: 2
```

## Agent/tool upgrades

Implemented upgrades:

- Robot keyword registry can expose approved built-in AegisQA keywords plus sanitized reference-corpus keywords.
- Automation generation reads the sanitized Robot style profile and annotates generated Robot files with style grounding.
- Telecom Robot generation filters generated keyword calls against approved/corpus-backed capabilities.
- Robot validation checks generated test steps against BuiltIn keywords and the approved/corpus keyword registry.
- Investigation coordinator adds execution-evidence-profile context when execution evidence is available.
- Report generator uses the report profile for post-execution guidance without changing legacy report summary behavior.

## Clean packaging

Clean packaging excludes:

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

The clean package keeps sanitized reference-corpus material under `fixtures/reference_corpus/` because it has passed the redaction pipeline.

## Verification

```bash
python -m pytest tests/test_sensitive_data_sanitizer.py tests/test_reference_corpus_grounding.py tests/test_reference_corpus_intake.py -q
# 12 passed

python -m ruff check scripts/sanitize_sensitive_data_repo.py scripts/generate_reference_corpus_profiles.py scripts/intake_reference_corpus.py tests/test_sensitive_data_sanitizer.py tests/test_reference_corpus_grounding.py tests/test_reference_corpus_intake.py
# passed

python scripts/verify_rag_corpus.py
# 43 chunks, all 8 probes retrieved
```

Frontend verification should be run with:

```bash
cd frontend
npm ci
npm run build
```

## Remaining gap

The failed execution example is not yet present. The current failed-execution profile correctly reports `has_failed_example=false`. Once a sanitized failed execution artifact is added, rerun:

```bash
python scripts/intake_reference_corpus.py --clean
python -m pytest -q
```
