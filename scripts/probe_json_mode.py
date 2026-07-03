"""Probe whether the vLLM endpoint accepts response_format=json_object cleanly."""
import json
import urllib.request
import urllib.error

BASE = "http://136.110.62.233:8000/v1"
MODEL = "ibnzterrell/Nvidia-Llama-3.1-Nemotron-70B-Instruct-HF-AWQ-INT4"

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are AegisQA."},
        {"role": "user", "content": "Return a JSON object with field 'ok' set to true."},
    ],
    "temperature": 0.1,
    "max_tokens": 200,
    "response_format": {"type": "json_object"},
}
req = urllib.request.Request(
    f"{BASE}/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer sk-local-vllm-no-auth"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.loads(r.read().decode())
    text = raw["choices"][0]["message"]["content"]
    print("HTTP 200 — response_format ACCEPTED")
    print("content:", repr(text[:200]))
    try:
        json.loads(text)
        print("content is valid JSON: True")
    except Exception as e:
        print("content is valid JSON: False —", e)
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code} — response_format REJECTED")
    print(e.read().decode()[:300])
except Exception as e:
    print("ERROR:", type(e).__name__, e)
