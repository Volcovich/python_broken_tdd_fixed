"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _parse_int(value: str) -> int | None:
    """Parse an integer string without raising exceptions."""
    stripped = value.strip()

    if not stripped:
        return None

    start = 0
    if stripped[0] in ("+", "-"):
        start = 1

    if start == len(stripped):
        return None

    digits = stripped[start:]
    if not all("0" <= character <= "9" for character in digits):
        return None

    number = 0
    for character in digits:
        number = number * 10 + ord(character) - ord("0")

    if start == 1 and stripped[0] == "-":
        return -number

    return number


def _line_error(position: int, line: dict[str, str]) -> str | None:
    """Return a readable reason why one order line is invalid, or None if it is fine."""
    for key in REQUIRED_LINE_KEYS:
        if key not in line:
            return f"Line {position} is missing a required key"

    sku = line["sku"]
    if not sku:
        return f"Line {position} has an empty sku"

    qty = _parse_int(line["qty"])
    if qty is None:
        return f"Invalid quantity in line {position}"
    if qty <= 0:
        return f"Quantity in line {position} must be positive"

    unit_price_kopecks = _parse_int(line["unit_price_kopecks"])
    if unit_price_kopecks is None:
        return f"Invalid price in line {position}"
    if unit_price_kopecks < 0:
        return f"Price in line {position} cannot be negative"

    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "Order has no lines"

    seen_skus: set[str] = set()

    for position, line in enumerate(lines, start=1):
        error = _line_error(position, line)
        if error is not None:
            return error

        sku = line["sku"]
        if sku in seen_skus:
            return f"Duplicate sku: {sku}"
        seen_skus.add(sku)

    if promo_code and promo_code not in PROMO_CODES:
        return "Unknown promo code"

    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "Unsupported shipping city"

    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = 0
    total_quantity = 0

    for line in lines:
        quantity = _parse_int(line["qty"])
        unit_price_kopecks = _parse_int(line["unit_price_kopecks"])

        if quantity is None or unit_price_kopecks is None:
            return None

        subtotal += quantity * unit_price_kopecks
        total_quantity += quantity

    tier_discount_percent = 0
    for threshold, discount_percent in TIER_DISCOUNTS:
        if total_quantity >= threshold:
            tier_discount_percent = discount_percent

    promo_discount_percent = PROMO_CODES.get(promo_code, 0)
    discount_percent = min(
        max(tier_discount_percent, promo_discount_percent),
        MAX_DISCOUNT_PERCENT,
    )

    discount = percent_of(subtotal, discount_percent)
    discounted_subtotal = subtotal - discount

    shipping = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS

    base = discounted_subtotal + shipping
    vat = percent_of(base, VAT_PERCENT)

    return base + vat
