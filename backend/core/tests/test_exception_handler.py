from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from core.api.exception_handler import giro_exception_handler
from core.domain.exceptions import GiroException


class GiroExceptionHandlerTests(SimpleTestCase):
    def test_domain_exception_uses_shared_error_shape(self):
        response = giro_exception_handler(
            GiroException(
                'Período indisponível.',
                fields={'vehicle_id': 'Veículo indisponível.'},
            ),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'code': 'BUSINESS_RULE_VIOLATION',
                'detail': 'Período indisponível.',
                'fields': {'vehicle_id': 'Veículo indisponível.'},
            },
        )

    def test_validation_error_is_localized_and_preserves_field_errors(self):
        response = giro_exception_handler(
            ValidationError({'starts_at': ['Formato inválido.']}),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
        self.assertEqual(response.data['detail'], 'Dados inválidos.')
        self.assertEqual(
            response.data['fields'],
            {'starts_at': ['Formato inválido.']},
        )
