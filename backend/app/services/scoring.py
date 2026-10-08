from typing import Tuple

def calculate_revo_score_and_audit(
    rating: float = 0.0,
    reviews_count: int = 0,
    has_website: bool = True,
    has_phone: bool = True,
    has_whatsapp: bool = False,
    scoring_rules: dict = None
) -> Tuple[int, str]:
    """
    Computes a Revo Lead Score (0 - 100) and an automated audit summary.
    """
    score = 100
    penalties = []

    rules = scoring_rules or {}
    missing_web_penalty = rules.get("missing_website_penalty", 10)
    low_rating_penalty = rules.get("low_rating_penalty", 15)
    low_reviews_penalty = rules.get("low_reviews_penalty", 20)

    if not has_website:
        score -= missing_web_penalty
        penalties.append("Отсутствует веб-сайт компании")

    if rating > 0 and rating < 4.0:
        score -= low_rating_penalty
        penalties.append(f"Низкий рейтинг ({rating}★)")

    if reviews_count < 20:
        score -= low_reviews_penalty
        penalties.append(f"Недостаточно отзывов ({reviews_count} шт.)")

    if not has_phone:
        score -= 15
        penalties.append("Отсутствует прямой телефон связи")

    if not has_whatsapp:
        score -= 5
        penalties.append("Нет прямого подключения к WhatsApp")

    score = max(0, min(100, score))

    if penalties:
        audit_notes = f"Выявленные уязвимости для оффера: {'; '.join(penalties)}. Высокая конверсия при предложении систем авто-сбора отзывов и CRM."
    else:
        audit_notes = "Отличная карточка компании. Высокий потенциал для премиального B2B сервиса."

    return score, audit_notes
