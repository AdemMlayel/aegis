"""Reproduce the workflow-path failure: a LARGE-output generation request.

The short 16-token probe succeeds, but the real workflow asks for up to
~1500 output tokens on a 70B model. This times a realistic large-output call
to see whether long/idle generations get dropped (ETIMEDOUT) where short ones
don't — distinguishing an idle-connection/firewall drop from a code issue.
"""
import json
import os
import time
import urllib.request

BASE_URL = os.getenv("AEGISQA_PROBE_BASE_URL", "http://127.0.0.1:8000/v1")
URL = f"{BASE_URL.rstrip('/')}/chat/completions"

# A longer prompt + large max_tokens to force a slow generation.
prompt = (
    "You are a QA requirement analyst. Analyze this ticket in detail: A banking "
    "customer requests a refund to their original payment method. Enumerate "
    "preconditions, actors, expected outcomes, error scenarios, data constraints, "
    "and performance expectations. Be thorough and write several paragraphs."
)
for max_tokens in (16, 512, 1500):
    payload = {
        "model": "ibnzterrell/Nvidia-Llama-3.1-Nemotron-70B-Instruct-HF-AWQ-INT4",
        "messages": [
            {"role": "system", "content": "You are AegisQA."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer LOCAL_PLACEHOLDER_TOKEN",
        },
        method="POST",
    )
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:  # noqa: S310
            d = json.loads(r.read().decode("utf-8"))
        out = d["choices"][0]["message"]["content"]
        usage = d.get("usage", {})
        print(f"max_tokens={max_tokens:>4}: OK in {time.perf_counter()-t:6.2f}s "
              f"(completion_tokens={usage.get('completion_tokens')}, chars={len(out)})")
    except Exception as e:  # noqa: BLE001
        print(f"max_tokens={max_tokens:>4}: FAILED in {time.perf_counter()-t:6.2f}s "
              f"-> {type(e).__name__}: {e}")
