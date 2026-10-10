import httpx

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def debug():
    try:
        resp = httpx.get(f"{BASE_URL}/leads", timeout=15.0)
        print("Status code:", resp.status_code)
        print("Response headers:", resp.headers)
        print("Response text:", resp.text)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    debug()
