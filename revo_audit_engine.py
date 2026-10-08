"""
revo_audit_engine.py — Модуль технической оценки и аудита бизнеса на Google Картах
================================================================================
Рассчитывает детальный балл качества карточки (Revo Score 0-100%), упущенную выручку
и формирует аналитические показатели для персонального отчета.
"""

def calculate_revo_score(lead_data: dict) -> dict:
    """
    Рассчитывает оценку профиля на основе 4 блоков:
    1. Reputation & Review Rate (30%): Рейтинг и количество отзывов
    2. Profile Completeness (30%): Сайт, телефон, адреса, полнота
    3. Search Visibility & Dominance (20%): Лидерство в локальном поиске
    4. Retention & Mobile Readiness (20%): Готовность к повторным продажам
    """
    company_name = lead_data.get("company_name", "Бизнес")
    rating = float(lead_data.get("rating", 0.0))
    reviews_count = int(lead_data.get("reviews_count", 0))
    website = lead_data.get("website", "").strip()
    phone = lead_data.get("phone", "").strip()

    # 1. Оценка репутации (0-30 баллов)
    reputation_points = 0
    if rating >= 4.8:
        reputation_points += 15
    elif rating >= 4.4:
        reputation_points += 10
    elif rating >= 4.0:
        reputation_points += 5

    if reviews_count >= 150:
        reputation_points += 15
    elif reviews_count >= 50:
        reputation_points += 10
    elif reviews_count >= 15:
        reputation_points += 5
    elif reviews_count > 0:
        reputation_points += 2

    # 2. Оценка полноты профиля (0-30 баллов)
    completeness_points = 0
    if website:
        completeness_points += 15
    if phone:
        completeness_points += 15

    # 3. Оценка видимости в поиске (0-20 баллов)
    visibility_points = 0
    if rating >= 4.5 and reviews_count >= 60:
        visibility_points = 20
    elif rating >= 4.2 and reviews_count >= 25:
        visibility_points = 12
    elif reviews_count > 5:
        visibility_points = 6
    else:
        visibility_points = 2

    # 4. Оценка Retention & повторных клиентов (0-20 баллов)
    # Если нет отзывов и сайта — у заведения нулевая система ретеншн
    retention_points = 0
    if reviews_count >= 100:
        retention_points = 15
    elif reviews_count >= 30:
        retention_points = 8
    else:
        retention_points = 3

    total_score = reputation_points + completeness_points + visibility_points + retention_points
    total_score = min(max(total_score, 18), 98) # Диапазон от 18% до 98%

    # Анализ узких мест (Bottlenecks)
    bottlenecks = []
    if reviews_count < 30:
        bottlenecks.append(f"Критически мало отзывов на Google Картах (всего {reviews_count})")
    elif rating < 4.4:
        bottlenecks.append(f"Низкий средний рейтинг ({rating}★ из 5.0)")

    if not website:
        bottlenecks.append("Отсутствует официальный сайт в карточке бизнеса")

    bottlenecks.append("Отсутствует автоматическая система сбора 5★ отзывов")
    bottlenecks.append("Нет приложения и системы лояльности для повторных продаж (Retention)")

    # Расчет упущенной выручки и роста
    if total_score < 45:
        potential_loss_pct = "50 – 75%"
        growth_factor = "+2.8x"
        status_label = "Критический потенциал роста"
        status_color = "#EF4444" # Red
    elif total_score < 70:
        potential_loss_pct = "35 – 55%"
        growth_factor = "+1.9x"
        status_label = "Высокий потенциал роста"
        status_color = "#F59E0B" # Amber
    else:
        potential_loss_pct = "20 – 35%"
        growth_factor = "+1.4x"
        status_label = "Умеренный потенциал"
        status_color = "#10B981" # Emerald

    return {
        "company_name": company_name,
        "business_type": lead_data.get("business_type", "Сфера услуг"),
        "overall_score": total_score,
        "reputation_score": int((reputation_points / 30) * 100),
        "completeness_score": int((completeness_points / 30) * 100),
        "visibility_score": int((visibility_points / 20) * 100),
        "retention_score": int((retention_points / 20) * 100),
        "potential_loss_pct": potential_loss_pct,
        "growth_factor": growth_factor,
        "status_label": status_label,
        "status_color": status_color,
        "rating": rating,
        "reviews_count": reviews_count,
        "bottlenecks": bottlenecks,
    }


if __name__ == "__main__":
    test_lead = {
        "company_name": "Beautify Salon Dubai",
        "business_type": "Beauty Salon",
        "rating": 4.1,
        "reviews_count": 18,
        "website": "https://beautifysalon.ae",
        "phone": "+97141234567"
    }
    result = calculate_revo_score(test_lead)
    print("Test Audit Score:", result)
