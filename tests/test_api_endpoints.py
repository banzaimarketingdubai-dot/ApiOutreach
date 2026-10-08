"""
test_api_endpoints.py — Автоматическое тестирование всех REST API ручек (Railway/Local)
"""

import sys
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

RAILWAY_BASE_URL = "https://web-production-c4d98.up.railway.app"

def test_api_suite(base_url=RAILWAY_BASE_URL):
    print(f"\n📡 [1/2] RUNNING API DIAGNOSTIC SUITE ON: {base_url}\n" + "-" * 55)
    passed = 0
    total = 0

    # 1. Healthcheck GET /
    total += 1
    try:
        r = requests.get(f"{base_url}/", timeout=10)
        if r.status_code == 200 and r.json().get("status") == "online":
            print(f"  ✅ [GET  /] Healthcheck Root -> 200 OK (Status: online)")
            passed += 1
        else:
            print(f"  ❌ [GET  /] Healthcheck Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /] Healthcheck Failed: {e}")

    # 2. Apify Account Balance GET /api/v1/apify/balance
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/apify/balance", timeout=15)
        if r.status_code == 200 and r.json().get("connected") is True:
            data = r.json()
            print(f"  ✅ [GET  /api/v1/apify/balance] Apify Balance -> 200 OK (Plan: {data.get('plan_name')}, Remaining: ${data.get('remaining_usd')})")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/apify/balance] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/apify/balance] Failed: {e}")

    # 3. AI Strategist POST /api/v1/ai/strategy
    total += 1
    try:
        payload = {
            "user_goal": "We want to collect high-ticket dental clinics in Dubai",
            "geo": "Dubai",
            "additional_notes": "Focus on implants and veneers"
        }
        r = requests.post(f"{base_url}/api/v1/ai/strategy", json=payload, timeout=20)
        if r.status_code == 200 and r.json().get("status") == "success":
            name = r.json().get("recommendation", {}).get("campaign_name", "")
            print(f"  ✅ [POST /api/v1/ai/strategy] AI Strategist -> 200 OK ('{name}')")
            passed += 1
        else:
            print(f"  ❌ [POST /api/v1/ai/strategy] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [POST /api/v1/ai/strategy] Failed: {e}")

    # 4. Create Campaign POST /api/v1/campaigns
    total += 1
    try:
        payload = {
            "campaign_name": "Test Diagnostic Campaign",
            "target_geo": "Dubai",
            "target_niches": ["Dental Clinics"],
            "ai_config": {
                "campaign_name": "Test Diagnostic Campaign",
                "target_geo": "Dubai",
                "target_niches": ["Dental Clinics"],
                "search_queries": ["Dental Clinic in Dubai"],
                "sources": ["gmaps"],
                "custom_variables": []
            }
        }
        r = requests.post(f"{base_url}/api/v1/campaigns", json=payload, timeout=15)
        if r.status_code in [200, 201]:
            print(f"  ✅ [POST /api/v1/campaigns] Campaign Creation -> HTTP {r.status_code} OK")
            passed += 1
        else:
            print(f"  ❌ [POST /api/v1/campaigns] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [POST /api/v1/campaigns] Failed: {e}")

    # 5. Fetch Leads GET /api/v1/leads
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/leads", timeout=10)
        if r.status_code == 200:
            count = len(r.json().get("leads", []))
            print(f"  ✅ [GET  /api/v1/leads] Fetch Master Data -> 200 OK ({count} leads found)")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/leads] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/leads] Failed: {e}")

    # 6. Export CSV GET /api/v1/export/csv
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/export/csv", timeout=10)
        if r.status_code == 200:
            print(f"  ✅ [GET  /api/v1/export/csv] Export CSV -> 200 OK (Content-Type: csv)")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/export/csv] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/export/csv] Failed: {e}")

    # 7. Vault Status GET /api/v1/settings/vault
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/settings/vault", timeout=10)
        if r.status_code == 200:
            print(f"  ✅ [GET  /api/v1/settings/vault] Vault Status -> HTTP 200 OK")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/settings/vault] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/settings/vault] Failed: {e}")

    # 8. Templates GET /api/v1/templates
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/templates", timeout=10)
        if r.status_code == 200:
            count = len(r.json())
            print(f"  ✅ [GET  /api/v1/templates] List Templates -> HTTP 200 OK ({count} templates)")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/templates] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/templates] Failed: {e}")

    # 9. Duplicates GET /api/v1/leads/tools/duplicates
    total += 1
    try:
        r = requests.get(f"{base_url}/api/v1/leads/tools/duplicates", timeout=15)
        if r.status_code == 200:
            groups = r.json()
            print(f"  ✅ [GET  /api/v1/leads/tools/duplicates] Merge Center -> HTTP 200 OK ({len(groups)} groups)")
            passed += 1
        else:
            print(f"  ❌ [GET  /api/v1/leads/tools/duplicates] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [GET  /api/v1/leads/tools/duplicates] Failed: {e}")

    # 10. AI Dry Run POST /api/v1/ai/dry-run
    total += 1
    try:
        payload = {
            "prompt_template": "Hello {{company_name}} in {{city}}",
            "lead_ids": [] # empty array is fine for a status check
        }
        r = requests.post(f"{base_url}/api/v1/ai/dry-run", json=payload, timeout=10)
        if r.status_code == 200:
            print(f"  ✅ [POST /api/v1/ai/dry-run] AI Sandbox -> HTTP 200 OK")
            passed += 1
        else:
            print(f"  ❌ [POST /api/v1/ai/dry-run] Failed: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"  ❌ [POST /api/v1/ai/dry-run] Failed: {e}")

    print("-" * 55)
    print(f"📊 RESULT: {passed}/{total} API tests passed.")
    return passed == total

if __name__ == "__main__":
    success = test_api_suite()
    sys.exit(0 if success else 1)
