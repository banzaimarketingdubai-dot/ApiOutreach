from fastapi import APIRouter, Depends
from celery.result import AsyncResult
from celery_app import celery_app
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        res = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": res.status,
            "result": res.result if res.ready() else None
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "result": None,
            "error": str(e)
        }
