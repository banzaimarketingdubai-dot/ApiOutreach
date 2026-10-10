import httpx

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def debug():
    auth_resp = httpx.post(f"{BASE_URL}/auth/google", json={"credential": "", "email": "ceo@gbpilot.top", "name": "CEO Admin"})
    token = auth_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = httpx.get(f"{BASE_URL}/leads?page_size=5", headers=headers)
    print("Status:", resp.status_code)
    print("Body:", resp.text)

if __name__ == "__main__":
    debug()
