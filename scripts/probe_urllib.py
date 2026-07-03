"""Isolate why the backend's urllib LLM call fails while curl succeeds.

Replicates OpenAICompatibleLLMProvider.complete()'s exact urllib request and
times it, printing proxy env and resolved address so we can tell a proxy /
DNS / IPv6 issue from a real endpoint problem.
"""
import json
import os
import socket
import time
import urllib.request

HOST = "34.142.189.205"
URL = f"http://{HOST}:8000/v1/chat/completions"

print("proxy env:", {k: v for k, v in os.environ.items() if "proxy" in k.lower()} or "(none)")
try:
    print("getaddrinfo:", socket.getaddrinfo(HOST, 8000, proto=socket.IPPROTO_TCP)[0][4])
except Exception as e:  # noqa: BLE001
    print("getaddrinfo FAILED:", e)

payload = {
    "model": "ibnzterrell/Nvidia-Llama-3.1-Nemotron-70B-Instruct-HF-AWQ-INT4",
    "messages": [
        {"role": "system", "content": "You are AegisQA."},
        {"role": "user", "content": "Reply with exactly: AEGIS_URLLIB_OK"},
    ],
    "temperature": 0.1,
    "max_tokens": 16,
}
req = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-local-vllm-no-auth",
    },
    method="POST",
)
t = time.perf_counter()
try:
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        d = json.loads(r.read().decode("utf-8"))
    print(f"urllib OK in {time.perf_counter() - t:.2f}s ->", repr(d["choices"][0]["message"]["content"]))
except Exception as e:  # noqa: BLE001
    print(f"urllib FAILED in {time.perf_counter() - t:.2f}s -> {type(e).__name__}: {e}")
