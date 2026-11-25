from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENT = Decimal('0.01')


def to_money(value: Decimal | int | str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise TypeError('O valor monetário deve ser Decimal, int ou str.')

    try:
        amount = Decimal(value)
        if not amount.is_finite():
            raise ValueError('O valor monetário deve ser finito.')
        return amount.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError('O valor monetário não é válido.') from exc
