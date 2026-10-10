import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        res = await client.get('https://web-production-c4d98.up.railway.app/api/v1/leads?skip=0&limit=100')
        data = res.json()
        for item in data:
            if "Kika-Style" in item.get('company_name', ''):
                print(item.get('company_name'), item.get('rating'), item.get('reviews_count'))

if __name__ == "__main__":
    asyncio.run(main())
