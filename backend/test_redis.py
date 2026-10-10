import asyncio
from app.db.session import engine, Base
from sqlalchemy import select
from app.models.lead import Lead
from app.services.rate_limiter import wait_for_gemini_capacity

async def test():
    print("Testing Redis Rate Limiter directly...")
    try:
        await wait_for_gemini_capacity()
        print("Rate limiter passed!")
    except Exception as e:
        print(f"Rate limiter failed! {type(e).__name__}: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(test())
