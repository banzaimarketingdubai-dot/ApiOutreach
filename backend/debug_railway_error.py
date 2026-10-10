import httpx

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def debug():
    auth_resp = httpx.post(f"{BASE_URL}/auth/google", json={"credential": "", "email": "ceo@gbpilot.top", "name": "CEO Admin"})
    token = auth_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = httpx.post(
        f"{BASE_URL}/outreach/funnels/start",
        json={"lead_ids": ["ebcc0d7e-ca07-4f5d-b21d-a415fc7a5f2e"], "funnel_type": "EMPATHY_AUDIT"},
        headers=headers
    )
    print("Funnel Start Status:", resp.status_code)
    print("Funnel Start Response:", resp.text)

if __name__ == "__main__":
    debug()
