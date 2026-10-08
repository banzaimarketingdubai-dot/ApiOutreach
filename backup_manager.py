"""
backup_manager.py — Система автоматического резервного копирования и защиты данных лидов
=======================================================================================
Гарантирует, что данные не будут потеряны или случайно перезаписаны.
Сохраняет резервные копии с меткой времени в папку `backups/`.
"""

import json
import logging
import os
import shutil
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

log = logging.getLogger(__name__)

BACKUP_DIR = "backups"

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup(filepath: str = "leads.json", tag: str = None) -> str:
    """
    Создаёт точную резервную копию указанного файла с меткой времени.
    Возвращает путь к бэкапу.
    """
    ensure_backup_dir()
    if not os.path.exists(filepath):
        log.warning(f"Невозможно сделать бэкап: файл '{filepath}' не найден.")
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    ext = os.path.splitext(filepath)[1]

    if tag:
        backup_name = f"{base_name}_{tag}_{timestamp}{ext}"
    else:
        backup_name = f"{base_name}_{timestamp}{ext}"

    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(filepath, backup_path)
    log.info(f"🛡️ Резервная копия создана: {backup_path}")
    return backup_path

def safe_save_json(data: list | dict, filepath: str = "leads.json", tag: str = None):
    """
    Безопасное сохранение данных:
    1. Если исходный файл существует, делает его бэкап.
    2. Записывает новые данные во временный файл и подменяет атомарно.
    3. Создает отдельный снапшот в папку backups/.
    """
    ensure_backup_dir()

    # 1. Бэкап существующего файла перед перезаписью
    if os.path.exists(filepath):
        create_backup(filepath, tag=tag or "auto_before_save")

    # 2. Атомарное сохранение
    temp_path = filepath + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp_path, filepath)
    log.info(f"💾 Данные безопасно сохранены в {filepath} ({len(data) if isinstance(data, list) else 1} записей)")

    # 3. Дополнительный снапшот после сохранения
    create_backup(filepath, tag=tag or "latest_snapshot")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if os.path.exists("leads.json"):
        backup_file = create_backup("leads.json", tag="manual_user_safety")
        print(f"OK: Backup created -> {backup_file}")
    else:
        print("leads.json not found")
