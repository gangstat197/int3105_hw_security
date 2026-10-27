import json
import os
import statistics
import time
from urllib.request import Request, urlopen


def request(url, headers=None, data=None):
    with urlopen(Request(url, headers=headers or {}, data=data), timeout=10) as response:
        return json.load(response)


token = request(
    "http://gateway/login", {"Content-Type": "application/json"},
    json.dumps({"username": "alice", "password": "password"}).encode(),
)["access_token"]
targets = {
    "Gateway": ("http://gateway/users", {"Authorization": f"Bearer {token}"}),
    "Direct": ("http://user-service:8000/users", {
        "X-User-ID": "1", "X-Gateway-Secret": os.environ["GATEWAY_SECRET"],
    }),
}
results = {}
for name, (url, headers) in targets.items():
    samples = []
    for _ in range(30):
        time.sleep(0.12)  # Stay below the gateway's 10 requests/second limit.
        start = time.perf_counter()
        request(url, headers)
        samples.append((time.perf_counter() - start) * 1000)
    results[name] = statistics.mean(samples)
    print(f"{name}: mean={results[name]:.2f} ms, median={statistics.median(samples):.2f} ms (30 requests)")
print(f"Mean gateway overhead: {results['Gateway'] - results['Direct']:.2f} ms")
print("Gateway includes JWT validation; direct calls use trusted internal headers.")
