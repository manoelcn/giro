from decimal import Decimal
from unittest import TestCase

from core.domain.money import to_money


class ToMoneyTests(TestCase):
    def test_quantizes_with_half_up_rounding(self):
        examples = (
            (Decimal('1.004'), Decimal('1.00')),
            (Decimal('1.005'), Decimal('1.01')),
            (Decimal('-1.005'), Decimal('-1.01')),
            ('12.3', Decimal('12.30')),
            (5, Decimal('5.00')),
        )

        for value, expected in examples:
            with self.subTest(value=value):
                self.assertEqual(to_money(value), expected)

    def test_rejects_invalid_values(self):
        for value in (1.25, True, Decimal('NaN'), Decimal('Infinity'), 'invalid'):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    to_money(value)
