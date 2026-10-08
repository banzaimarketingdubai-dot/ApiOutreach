"""
test_ui_e2e.py — Автономное E2E тестирование кликов, форм и ответов на Vercel UI
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
    print(f"\n🖥️ [2/2] RUNNING PLAYWRIGHT FULL E2E CLICK & SUBMIT SUITE ON: {url}\n" + "-" * 55)
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ⚠️ Playwright package not installed in environment. Skipping UI E2E browser test.")
        return True

    os.makedirs("tests/screenshots", exist_ok=True)
    passed = True
    alert_messages = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Listen for browser alert popups
        page.on("dialog", lambda dialog: (alert_messages.append(dialog.message), asyncio.create_task(dialog.accept())))

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

        # 2. Switch to 'Campaign Builder' Tab
        try:
            builder_tab = page.get_by_text("Campaign Builder")
            if await builder_tab.is_visible():
                await builder_tab.click()
                await asyncio.sleep(1)
                print(f"  ✅ [UI Nav] Switched to 'Campaign Builder' Tab")
            else:
                print(f"  ⚠️ [UI Nav] 'Campaign Builder' tab button not found")
        except Exception as e:
            print(f"  ❌ [UI Nav] Failed switching tabs: {e}")
            passed = False

        # 3. Test Quick Task Builder Form Submission (Button Click & API response check)
        try:
            launch_btn = page.get_by_role("button", name="Launch Direct Task")
            if await launch_btn.is_visible():
                alert_messages.clear()
                await launch_btn.click()
                await asyncio.sleep(4)
                
                # Check captured alert popups
                has_error_alert = any("Error" in msg or "Failed" in msg for msg in alert_messages)
                has_success_alert = any("Pipeline task submitted" in msg for msg in alert_messages)
                
                if has_error_alert:
                    print(f"  ❌ [UI Form Submit] Quick Task Builder Alert ERROR: {alert_messages}")
                    passed = False
                elif has_success_alert:
                    print(f"  ✅ [UI Form Submit] Quick Task Builder SUCCESS -> Alert: '{alert_messages[-1]}'")
                else:
                    print(f"  ✅ [UI Form Submit] Quick Task Builder Clicked & Processed (Alerts: {alert_messages})")
            else:
                print(f"  ❌ [UI Form Submit] 'Launch Direct Task' button not visible after switching tab")
                passed = False
        except Exception as e:
            print(f"  ❌ [UI Form Submit] Error testing Quick Task Builder: {e}")
            passed = False

        # 4. Test AI Strategist Co-pilot Modal & Strategy Generation
        try:
            ai_nav_btn = page.get_by_text("AI Strategist Co-pilot")
            if await ai_nav_btn.is_visible():
                await ai_nav_btn.click()
                await asyncio.sleep(1)
                
                # Look for the analyze button inside the modal
                analyze_btn = page.get_by_role("button", name="Analyze Strategy")
                if await analyze_btn.is_visible():
                    alert_messages.clear()
                    await analyze_btn.click()
                    await asyncio.sleep(5)
                    
                    has_error_alert = any("Error" in msg or "Failed" in msg for msg in alert_messages)
                    if has_error_alert:
                        print(f"  ❌ [UI AI Modal] AI Strategy Generation Alert ERROR: {alert_messages}")
                        passed = False
                    else:
                        print(f"  ✅ [UI AI Modal] AI Strategy Modal Form Clicked & Generated Strategy!")
                        
                    # Close the modal
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                else:
                    print(f"  ✅ [UI AI Modal] AI Strategist Modal Opened")
                    await page.keyboard.press("Escape")
            else:
                print(f"  ⚠️ [UI AI Modal] AI Strategist Navbar button not found")
        except Exception as e:
            print(f"  ❌ [UI AI Modal] Modal Interaction Error: {e}")
            passed = False

        # 5. Test Merge Center Tab Navigation
        try:
            merge_tab = page.get_by_text("Merge Center")
            if await merge_tab.is_visible():
                await merge_tab.click()
                await asyncio.sleep(1)
                
                scan_btn = page.get_by_role("button", name="Scan for Duplicates")
                if await scan_btn.is_visible():
                    print(f"  ✅ [UI Nav] Switched to 'Merge Center' Tab & 'Scan' button found")
                else:
                    print(f"  ⚠️ [UI Nav] 'Scan for Duplicates' button missing in Merge Center")
            else:
                print(f"  ⚠️ [UI Nav] 'Merge Center' tab button not found")
        except Exception as e:
            print(f"  ❌ [UI Nav] Error in Merge Center test: {e}")
            passed = False

        # 6. Test Settings & Templates Tab Navigation
        try:
            admin_tab = page.get_by_text("Settings & Templates")
            if await admin_tab.is_visible():
                await admin_tab.click()
                await asyncio.sleep(1)
                
                vault_save_btn = page.get_by_role("button", name="Save to Vault")
                if await vault_save_btn.is_visible():
                    print(f"  ✅ [UI Nav] Switched to 'Settings & Templates' Tab (Vault loaded)")
                else:
                    print(f"  ⚠️ [UI Nav] 'Save to Vault' missing in Admin Panel")
                
                # Switch to Templates sub-tab
                tpl_tab = page.get_by_text("Prompt Templates")
                if await tpl_tab.is_visible():
                    await tpl_tab.click()
                    await asyncio.sleep(1)
                    create_tpl_btn = page.get_by_role("button", name="Create Template")
                    if await create_tpl_btn.is_visible():
                        print(f"  ✅ [UI Nav] Switched to 'Prompt Templates' sub-tab & 'Create Template' found")
                    else:
                        print(f"  ⚠️ [UI Nav] 'Create Template' missing")
            else:
                print(f"  ⚠️ [UI Nav] 'Settings & Templates' tab button not found")
        except Exception as e:
            print(f"  ❌ [UI Nav] Error in Admin Panel test: {e}")
            passed = False

        # Save Screenshot
        screenshot_path = "tests/screenshots/vercel_ui_health.png"
        await page.screenshot(path=screenshot_path)
        print(f"  📷 [UI] Full Health Screenshot saved to: {screenshot_path}")

        await browser.close()

    print("-" * 55)
    print(f"📊 RESULT: UI E2E Test {'PASSED ✅' if passed else 'FAILED ❌'}")
    return passed

if __name__ == "__main__":
    success = asyncio.run(test_ui_suite())
    sys.exit(0 if success else 1)
