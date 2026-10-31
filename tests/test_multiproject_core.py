"""
test_multiproject_core.py — Тестирование ядра мультипроектности:
Проекты, Продукты, Аудитории и их связи.
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
from app.models.project import Project
from app.models.product import Product
from app.models.audience import Audience
from app.models.lead import Lead

def test_multiproject_schemas_and_models():
    print("\n🔍 1. Testing Multi-Project ORM Models initialization...")
    assert hasattr(Project, "products")
    assert hasattr(Project, "audiences")
    assert hasattr(Project, "leads")
    assert hasattr(Project, "outreach_campaigns")
    assert hasattr(Product, "project")
    assert hasattr(Audience, "project")
    assert hasattr(Audience, "leads")
    assert hasattr(Lead, "project_id")
    assert hasattr(Lead, "audience_id")
    print("  ✅ All ORM models and relationships verified!")

def test_api_routes_registration():
    print("\n🔍 2. Testing FastAPI Router Registration...")
    client = TestClient(app)
    
    # Check OpenAPI schema has new routes
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200, f"OpenAPI returned {response.status_code}"
    paths = response.json().get("paths", {})
    
    expected_routes = [
        "/api/v1/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/products",
        "/api/v1/products/{product_id}",
        "/api/v1/audiences",
        "/api/v1/audiences/{audience_id}",
        "/api/v1/audiences/{audience_id}/recalculate-stats"
    ]
    
    for route in expected_routes:
        assert route in paths, f"Route {route} not found in OpenAPI specs!"
        print(f"  ✅ Verified endpoint: {route}")
        
    print("  ✅ All Multi-Project API endpoints successfully registered!")

if __name__ == "__main__":
    test_multiproject_schemas_and_models()
    test_api_routes_registration()
    print("\n🎉 ALL MULTI-PROJECT CORE CHECKS PASSED!")
