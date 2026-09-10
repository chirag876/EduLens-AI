from decimal import ROUND_HALF_UP, Decimal


def round_to(value, decimal_places):
    rounding_format = '1.' + '0' * decimal_places
    return float(Decimal(str(value)).quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP))
