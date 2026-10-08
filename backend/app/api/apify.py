import httpx
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.core.config import settings

router = APIRouter()

@router.get("/balance")
async def get_apify_balance() -> Dict[str, Any]:
    """
    Fetch Apify account info, plan, monthly credit limit, and current usage.
    """
    token = settings.APIFY_API_TOKEN
    if not token:
        return {
            "status": "warning",
            "connected": False,
            "message": "Apify API Token is not configured in .env"
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Fetch user account & plan info
            user_resp = await client.get(f"https://api.apify.com/v2/users/me?token={token}")
            if user_resp.status_code != 200:
                raise HTTPException(status_code=user_resp.status_code, detail="Invalid Apify API Token")

            user_data = user_resp.json().get("data", {})
            plan = user_data.get("plan", {})
            plan_name = plan.get("tier", "FREE")
            monthly_limit = plan.get("monthlyUsageCreditsUsd", 5.0)

            # 2. Fetch monthly usage
            usage_resp = await client.get(f"https://api.apify.com/v2/users/me/usage/monthly?token={token}")
            used_usd = 0.0
            if usage_resp.status_code == 200:
                usage_data = usage_resp.json().get("data", {})
                used_usd = usage_data.get("totalUsageCreditsUsdAfterVolumeDiscount", 0.0)

            remaining_usd = max(0.0, monthly_limit - used_usd)
            used_percentage = round((used_usd / monthly_limit) * 100, 2) if monthly_limit > 0 else 0.0

            return {
                "status": "success",
                "connected": True,
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "plan_name": plan_name,
                "monthly_limit_usd": round(monthly_limit, 2),
                "used_usd": round(used_usd, 4),
                "remaining_usd": round(remaining_usd, 2),
                "used_percentage": used_percentage,
                "proxy_groups": user_data.get("proxy", {}).get("groups", [])
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Apify account API: {str(e)}")
