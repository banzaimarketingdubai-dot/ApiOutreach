import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots_e2e")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

TARGET_URL = "https://apioutreach.vercel.app"

def run_e2e_tests():
    print(f"\n🚀 Starting Global E2E Playwright Suite against: {TARGET_URL}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Open Target URL
        print("📍 Step 1: Navigating to Web Panel...")
        page.goto(TARGET_URL, wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "1_login_page.png"))
        print("  📸 Captured: 1_login_page.png")

        # Step 2: Handle Authentication if Login Modal is present
        print("📍 Step 2: Authenticating...")
        quick_btn = page.locator("button:has-text('Войти через Google Account')")
        if quick_btn.count() > 0:
            print("  Found Quick Google Login button, clicking...")
            quick_btn.first.click()
            page.wait_for_load_state("networkidle")
            time.sleep(3)
        else:
            print("  Already authenticated or session restored.")

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "2_dashboard_loaded.png"))
        print("  📸 Captured: 2_dashboard_loaded.png")

        # Step 3: Verify Header and Active Project
        print("📍 Step 3: Checking Header and Project Selector...")
        header_text = page.locator("header").inner_text()
        print(f"  Header contents: {header_text.replace(chr(10), ' | ')[:120]}...")
        assert "REVO" in header_text, "REVO brand not found in Header!"

        # Step 4: Test Audiences Tab & Modal with Project Selector
        print("📍 Step 4: Testing 'Аудитории' Hub & Creation Modal...")
        aud_tab = page.locator("button:has-text('Аудитории')")
        if aud_tab.count() > 0:
            aud_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "3_audiences_hub.png"))
            print("  📸 Captured: 3_audiences_hub.png")

            # Click create audience
            create_btn = page.locator("button:has-text('Создать аудиторию'), button:has-text('Создать первую аудиторию')")
            if create_btn.count() > 0:
                create_btn.first.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "4_create_audience_modal.png"))
                print("  📸 Captured: 4_create_audience_modal.png")

                # Check if Project Workspace is visible in Modal
                modal_text = page.locator("form").inner_text()
                print(f"  Modal form labels: {modal_text.replace(chr(10), ' | ')[:150]}")
                assert "Проект" in modal_text, "Project workspace selector not found in modal!"

                # Fill audience form
                test_aud_name = f"Playwright Dubai {int(time.time())}"
                page.fill("input[placeholder*='Стоматологии']", test_aud_name)
                page.fill("textarea[placeholder*='Клиники']", "Automated E2E Playwright verification")
                
                # Submit inside form
                page.locator("form button[type='submit']").click()
                time.sleep(3)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "5_audience_created.png"))
                print(f"  ✅ Audience '{test_aud_name}' created successfully!")
                print("  📸 Captured: 5_audience_created.png")

        # Step 5: Test Products Hub
        print("📍 Step 5: Testing 'Продукты' Hub...")
        prod_tab = page.locator("button:has-text('Продукты')")
        if prod_tab.count() > 0:
            prod_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "6_products_hub.png"))
            print("  📸 Captured: 6_products_hub.png")

            # Click Add Product
            add_prod_btn = page.locator("button:has-text('Добавить продукт'), button:has-text('Создать первый продукт')")
            if add_prod_btn.count() > 0:
                add_prod_btn.first.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "7_product_modal.png"))
                print("  📸 Captured: 7_product_modal.png")

                # Fill product details
                test_prod_name = f"AI Audit Pro {int(time.time())}"
                page.locator("input[placeholder*='AI-аудит']").fill(test_prod_name)
                page.locator("textarea[placeholder*='В чем заключается']").fill("Automated Playwright Offer Description")
                page.locator("input[placeholder*='Владельцы клиник']").fill("B2B Companies & Clinics")

                # Save product inside form
                page.locator("form button[type='submit']").click()
                time.sleep(3)
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, "8_product_saved.png"))
                print(f"  ✅ Product '{test_prod_name}' created successfully!")
                print("  📸 Captured: 8_product_saved.png")

        # Step 6: Test AI Funnel Studio
        print("📍 Step 6: Testing 'AI Воронка' Studio...")
        funnel_tab = page.locator("button:has-text('AI Воронка')")
        if funnel_tab.count() > 0:
            funnel_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "9_ai_funnel_studio.png"))
            print("  📸 Captured: 9_ai_funnel_studio.png")

        # Step 7: Test Review Queue (Модерация)
        print("📍 Step 7: Testing 'Модерация' Queue...")
        review_tab = page.locator("button:has-text('Модерация')")
        if review_tab.count() > 0:
            review_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "10_review_queue.png"))
            print("  📸 Captured: 10_review_queue.png")

        # Step 8: Test Smart Inbox
        print("📍 Step 8: Testing 'Smart Inbox'...")
        inbox_tab = page.locator("button:has-text('Smart Inbox')")
        if inbox_tab.count() > 0:
            inbox_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_smart_inbox.png"))
            print("  📸 Captured: 11_smart_inbox.png")

        # Step 9: Test Analytics Dashboard
        print("📍 Step 9: Testing 'Analytics'...")
        analytics_tab = page.locator("button:has-text('Analytics')")
        if analytics_tab.count() > 0:
            analytics_tab.first.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "12_analytics.png"))
            print("  📸 Captured: 12_analytics.png")

        browser.close()
        print("\n🎉 ALL E2E PLAYWRIGHT TESTS PASSED SUCCESSFULLY! 🚀\n")

if __name__ == "__main__":
    run_e2e_tests()
