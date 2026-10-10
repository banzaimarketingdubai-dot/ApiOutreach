import time
import asyncio
import os
from redis.asyncio import Redis

# Reuse REDIS_URL from Railway or fallback to CELERY_BROKER_URL or localhost
REDIS_URL = os.getenv("REDIS_URL", os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))
redis_client = Redis.from_url(REDIS_URL)

async def wait_for_gemini_capacity():
    """
    Ensures that we don't exceed 15 requests per minute globally for Gemini API.
    Uses Redis to track timestamps of recent requests across all modules (FastAPI, Celery workers).
    """
    key = "gemini_api_requests"
    limit = 14 # 14 requests per 60 seconds to be safe under the 15 RPM limit
    period = 60 
    
    while True:
        now = time.time()
        
        # Pipeline for atomic operations
        async with redis_client.pipeline(transaction=True) as pipe:
            # Remove timestamps older than 60 seconds
            pipe.zremrangebyscore(key, 0, now - period)
            # Count requests in the last 60 seconds
            pipe.zcard(key)
            results = await pipe.execute()
            
            count = results[1]
            
            if count < limit:
                # We have capacity, add current timestamp
                # Add tiny fractional jitter to prevent key collision if exact same timestamp
                import random
                unique_now = now + random.uniform(0.0001, 0.0099)
                
                pipe.zadd(key, {str(unique_now): now})
                pipe.expire(key, period)
                await pipe.execute()
                break
            
        # If we hit the limit, wait before retrying to prevent cooldown/429
        await asyncio.sleep(2)
