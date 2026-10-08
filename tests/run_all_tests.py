"""
run_all_tests.py — Главный оркестратор автономной диагностики и авто-тестирования Revo Platform
"""

import sys
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from test_api_endpoints import test_api_suite
from test_ui_e2e import test_ui_suite

def main():
    print("=" * 65)
    print("🚀 REVO MASTER DATA PLATFORM — FULL DIAGNOSTIC SUITE")
    print("=" * 65)

    api_ok = test_api_suite()
    ui_ok = asyncio.run(test_ui_suite())

    print("\n" + "=" * 65)
    if api_ok and ui_ok:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! SYSTEM IS 100% HEALTHY.")
        print("=" * 65)
        sys.exit(0)
    else:
        print("⚠️ SOME TESTS FAILED! Check logs above for details.")
        print("=" * 65)
        sys.exit(1)

if __name__ == "__main__":
    main()
