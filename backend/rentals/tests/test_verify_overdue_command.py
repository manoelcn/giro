from datetime import UTC, datetime
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


class VerifyOverdueCommandTests(SimpleTestCase):
    @patch('rentals.management.commands.verify_overdue.get_rental_service')
    def test_passes_injected_timestamp_to_service(self, get_service):
        service = Mock()
        service.verify_overdue.return_value = []
        get_service.return_value = service
        output = StringIO()

        call_command(
            'verify_overdue',
            now='2030-01-04T11:00:01Z',
            stdout=output,
        )

        service.verify_overdue.assert_called_once_with(
            datetime(2030, 1, 4, 11, 0, 1, tzinfo=UTC),
        )
        self.assertIn('0 reserva(s)', output.getvalue())

    def test_rejects_invalid_timestamp(self):
        with self.assertRaises(CommandError):
            call_command('verify_overdue', now='not-a-timestamp')
