"""Clean example module for the governed-audit demo PR."""


def price_with_discount(price: float, discount_pct: float) -> float:
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount must be 0-100")
    return round(price * (1 - discount_pct / 100), 2)


def is_admin(user: dict) -> bool:
    return user.get("role") == "admin"
