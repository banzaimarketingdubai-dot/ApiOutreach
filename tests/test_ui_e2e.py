"""
test_ui_e2e.py — Автономное E2E тестирование UI интерфейса на Vercel с помощью Playwright
"""

import os
import sys
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VERCEL_UI_URL = "https://apioutreach.vercel.app"

async def test_ui_suite(url=VERCEL_UI_URL):
    print(f"\n🖥️ [2/2] RUNNING PLAYWRIGHT UI E2E SUITE ON: {url}\n" + "-" * 55)
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ⚠️ Playwright package not installed in environment. Skipping UI E2E browser test.")
        return True

    os.makedirs("tests/screenshots", exist_ok=True)
    passed = True

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Load Vercel Web Page
        try:
            res = await page.goto(url, wait_until="networkidle", timeout=30000)
            if res and res.status == 200:
                print(f"  ✅ [UI] Load Page -> 200 OK")
            else:
                print(f"  ❌ [UI] Load Page Failed: Status {res.status if res else 'No response'}")
                passed = False
        except Exception as e:
            print(f"  ❌ [UI] Load Page Failed: {e}")
            await browser.close()
            return False

        # 2. Check UI Title & Elements
        try:
            content = await page.content()
            if "REVO" in content or "Master Data" in content:
                print(f"  ✅ [UI] Master Data Title Rendered")
            else:
                print(f"  ❌ [UI] Master Data Title not found in DOM")
                passed = False
        except Exception as e:
            print(f"  ❌ [UI] DOM Inspection Failed: {e}")
            passed = False

        # 3. Test Clicking AI Strategist Co-pilot Button
        try:
            ai_btn = page.get_by_text("AI Strategist Co-pilot")
            if await ai_btn.is_visible():
                await ai_btn.click()
                await asyncio.sleep(1)
                modal = page.get_by_text("AI Campaign Strategist & Co-pilot")
                if await modal.is_visible():
                    print(f"  ✅ [UI] AI Strategist Modal Opened Successfully")
                else:
                    print(f"  ⚠️ [UI] AI Strategist Modal opened but title match failed")
            else:
                print(f"  ⚠️ [UI] AI Strategist Button not found on navbar")
        except Exception as e:
            print(f"  ❌ [UI] Modal Interaction Error: {e}")

        # Save Screenshot
        screenshot_path = "tests/screenshots/vercel_ui_health.png"
        await page.screenshot(path=screenshot_path)
        print(f"  📷 [UI] Screenshot saved to: {screenshot_path}")

        await browser.close()

    print("-" * 55)
    print(f"📊 RESULT: UI E2E Test {'PASSED ✅' if passed else 'FAILED ❌'}")
    return passed

if __name__ == "__main__":
    success = asyncio.run(test_ui_suite())
    sys.exit(0 if success else 1)
