import httpx

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def test_endpoints():
    endpoints = [
        "/outreach/analytics",
        "/campaigns",
        "/templates",
        "/auth/me"
    ]
    for ep in endpoints:
        resp = httpx.get(f"{BASE_URL}{ep}", timeout=10.0)
        print(f"{ep}: status={resp.status_code}, body={resp.text[:100]}")

if __name__ == "__main__":
    test_endpoints()
