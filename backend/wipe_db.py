import httpx
import asyncio

async def main():
    base_url = "https://web-production-c4d98.up.railway.app/api/v1"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        login_data = {
            "email": "admin@revo.ai",
            "password": "admin123"
        }
        resp = await client.post(f"{base_url}/auth/login", json=login_data)
        if resp.status_code != 200:
            print("Failed to login:", resp.text)
            return
            
        token = resp.json().get("access_token")
        print("Got token:", token[:10] + "...")
        
        # 2. Wipe DB
        print("Wiping DB...")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.delete(f"{base_url}/leads/tools/clean_all", headers=headers)
        
        if resp.status_code == 204:
            print("Successfully wiped all leads!")
        else:
            print("Failed to wipe:", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(main())
