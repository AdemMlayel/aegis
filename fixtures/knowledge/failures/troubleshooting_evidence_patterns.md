# Troubleshooting Evidence Patterns

Synthetic reference for what good troubleshooting evidence looks like in AegisQA. Used to
shape investigation output and to teach the assistant which evidence carries weight.

## Evidence kinds

- robot_result — per-test status, message, duration; the strongest signal for a concrete
  failure.
- artifact — references to output.xml, log.html, report.html, or captured traces.
- knowledge_ref — retrieved synthetic documentation that informed generation.
- memory_ref — prior archived workflow outcomes for the same domain.
- model_trace — which prompt and provider produced a given artifact.

## Weighting principle

Direct execution evidence outweighs inferred evidence. A finding linked to a failing
robot_result is more trustworthy than one inferred from a single log line. Historical
matches against known failure signatures add corroboration but do not by themselves prove
a root cause.

## Good vs weak evidence

- Good: "Test VR-DIA-001 failed with 'Session-Id mismatch'; linked robot_result and a
  KF-002 historical match both point to a correlation defect."
- Weak: "The log mentions an error, so the application is probably broken." This lacks a
  linked result, a category, and a historical reference.

## Correlation

When multiple findings share a timestamp window or a common component placeholder, note
the correlation explicitly; correlated failures often share a single root cause.

## Pitfalls

- Do not raise confidence on volume of logs alone.
- Do not include raw payloads; summarize and sanitize every excerpt.
- Always state the cheap check that would confirm the leading hypothesis.
