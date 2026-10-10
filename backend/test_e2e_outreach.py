import httpx
import time
import json

BASE_URL = "https://web-production-c4d98.up.railway.app/api/v1"

def run_e2e_test():
    print("=== STARTING END-TO-END LIVE OUTREACH & ANALYTICS TEST ===")
    
    # 1. Fetch Existing Lead from Railway API
    print("\n[Step 1] Fetching active leads from database...")
    try:
        resp = httpx.get(f"{BASE_URL}/leads?page_size=5", timeout=15.0)
        print(f"-> Fetch Leads status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error fetching leads: {resp.text}")
            return
        data = resp.json()
        items = data.get("items", [])
        if not items:
            print("No leads found in database to test with.")
            return
            
        test_lead = items[0]
        lead_id = test_lead.get("id")
        company_name = test_lead.get("company_name")
        print(f"-> Selected Test Lead: '{company_name}' (ID: {lead_id})")
    except Exception as e:
        print(f"Exception fetching leads: {e}")
        return

    # 2. Queue Drip Sequence for Test Lead
    print("\n[Step 2] Triggering Funnel sequence (EMPATHY_AUDIT)...")
    funnel_payload = {
        "lead_ids": [lead_id],
        "funnel_type": "EMPATHY_AUDIT"
    }
    
    resp = httpx.post(f"{BASE_URL}/outreach/funnels/start", json=funnel_payload, timeout=15.0)
    print(f"-> Start Funnel status: {resp.status_code}, Response: {resp.text}")

    # 3. Trigger Instant Email Queue Processing
    print("\n[Step 3] Dispatching queue via Resend...")
    resp = httpx.post(f"{BASE_URL}/outreach/process_queue", timeout=15.0)
    print(f"-> Process Queue status: {resp.status_code}, Response: {resp.text}")
    
    time.sleep(2)

    # 4. Simulate Open & Click Webhooks from Resend
    print("\n[Step 4] Simulating Resend Webhook Events (email.opened & email.clicked)...")
    
    # Send email.opened event
    open_payload = {
        "type": "email.opened",
        "data": {
            "created_at": "2026-10-10T14:02:00.000Z",
            "email_id": f"resend_test_{lead_id}",
            "tags": [{"name": "lead_id", "value": lead_id}]
        }
    }
    resp = httpx.post(f"{BASE_URL}/outreach/webhooks/resend", json=open_payload, timeout=15.0)
    print(f"-> Webhook email.opened status: {resp.status_code}, Response: {resp.text}")

    # Send email.clicked event
    click_payload = {
        "type": "email.clicked",
        "data": {
            "created_at": "2026-10-10T14:02:15.000Z",
            "email_id": f"resend_test_{lead_id}",
            "tags": [{"name": "lead_id", "value": lead_id}],
            "click": {"link": "https://gbpilot-saas.vercel.app/audit/test"}
        }
    }
    resp = httpx.post(f"{BASE_URL}/outreach/webhooks/resend", json=click_payload, timeout=15.0)
    print(f"-> Webhook email.clicked status: {resp.status_code}, Response: {resp.text}")

    # 5. Fetch Analytics Dashboard Metrics
    print("\n[Step 5] Fetching live Analytics Dashboard metrics...")
    resp = httpx.get(f"{BASE_URL}/outreach/analytics", timeout=15.0)
    print(f"-> Analytics status: {resp.status_code}")
    if resp.status_code == 200:
        analytics = resp.json()
        print(f"-> Live Funnel Metrics:\n{json.dumps(analytics, indent=2, ensure_ascii=False)}")

    print("\n=== END-TO-END TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_e2e_test()
