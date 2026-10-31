"""
test_stage4_stage5.py — Комплексное тестирование Stage 4 (Review Queue & Smart Inbox) и Stage 5 (Project Analytics).
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend directory is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.models.inbound_reply import InboundReply, ReplyIntent
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_sequence import EmailSequence

def test_models():
    print("\n🔍 1. Testing Stage 4 & 5 ORM Models...")
    assert hasattr(InboundReply, "intent")
    assert hasattr(InboundReply, "ai_draft_response")
    assert hasattr(InboundReply, "ai_analysis")
    assert hasattr(InboundReply, "is_handled")
    assert hasattr(OutreachCampaign, "is_manual_review_required")
    assert hasattr(OutreachCampaign, "schedule_config")
    print("  ✅ All ORM models and fields verified successfully!")

def test_openapi_routes():
    print("\n🔍 2. Testing Stage 4 & 5 Route Declarations in OpenAPI...")
    client = TestClient(app)
    res = client.get("/api/v1/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})

    expected_routes = [
        "/api/v1/outreach/launch-multi-campaign",
        "/api/v1/outreach/review-queue",
        "/api/v1/outreach/review-queue/approve",
        "/api/v1/outreach/review-queue/reject",
        "/api/v1/outreach/inbox",
        "/api/v1/outreach/inbox/simulate-reply",
        "/api/v1/outreach/analytics"
    ]

    for r in expected_routes:
        assert r in paths, f"Route '{r}' is missing from OpenAPI schema!"
        print(f"  ✓ {r} registered.")

if __name__ == "__main__":
    test_models()
    test_openapi_routes()
    print("\n🎉 All Stage 4 & Stage 5 core validations passed!")
