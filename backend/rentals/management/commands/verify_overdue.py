from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rentals.services.factories import get_rental_service


class Command(BaseCommand):
    help = 'Atualiza locações atrasadas e identifica reservas futuras afetadas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--now',
            help='Instante ISO 8601 usado na verificação (opcional).',
        )

    def handle(self, *args, **options):
        now_text = options.get('now')
        now = parse_datetime(now_text) if now_text else timezone.now()
        if now is None:
            raise CommandError('O instante --now deve usar o formato ISO 8601.')
        if timezone.is_naive(now):
            now = timezone.make_aware(now)

        alerts = get_rental_service().verify_overdue(now)
        return f'Verificação concluída. {len(alerts)} reserva(s) futura(s) afetada(s).'
