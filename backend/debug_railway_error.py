import httpx

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def debug():
    resp = httpx.post(f"{BASE_URL}/auth/google", json={"credential": "", "email": "ceo@gbpilot.top", "name": "CEO Admin"})
    print("Google Auth Status:", resp.status_code)
    print("Google Auth Response:", resp.text)

if __name__ == "__main__":
    debug()
