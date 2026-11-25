from core.domain.exceptions import GiroException


class ConflictingReservationException(GiroException):
    code = 'RESERVATION_CONFLICT'
    status_code = 409
    default_detail = 'O veículo já está ocupado nesse período.'


class InvalidStateTransitionException(GiroException):
    code = 'INVALID_STATE_TRANSITION'
    status_code = 409
    default_detail = 'A operação não é permitida no estado atual.'


class CancellationDeadlineExceededException(GiroException):
    code = 'CANCELLATION_DEADLINE_EXCEEDED'
    status_code = 409
    default_detail = 'A retirada já foi registrada; use o fluxo de devolução.'


class InsufficientDepositException(GiroException):
    code = 'INSUFFICIENT_DEPOSIT'
    status_code = 422
    default_detail = 'A caução paga é inferior ao mínimo exigido.'


class PendingInspectionException(GiroException):
    code = 'PENDING_INSPECTION'
    status_code = 422
    default_detail = 'A vistoria obrigatória ainda não foi registrada.'


class VehicleUnavailableException(GiroException):
    code = 'VEHICLE_UNAVAILABLE'
    status_code = 409
    default_detail = 'O veículo não está operacional para locação.'


class QuoteChangedException(GiroException):
    code = 'QUOTE_CHANGED'
    status_code = 409
    default_detail = 'O valor da cotação mudou; consulte uma nova oferta.'


class CustomerIneligibleException(GiroException):
    code = 'CUSTOMER_INELIGIBLE'
    status_code = 422
    default_detail = 'O cliente não atende aos requisitos para locação.'


class DatabaseContentionException(GiroException):
    code = 'DATABASE_CONTENTION'
    status_code = 503
    default_detail = 'O banco está ocupado. Tente a operação novamente.'


class RentalNotFoundException(GiroException):
    code = 'NOT_FOUND'
    status_code = 404
    default_detail = 'Locação não encontrada.'


class PendingBalanceException(GiroException):
    code = 'PENDING_BALANCE'
    status_code = 409
    default_detail = 'A locação não pode ser finalizada enquanto houver saldo pendente.'


class IntegrationNotConfiguredException(GiroException):
    code = 'INTEGRATION_NOT_CONFIGURED'
    status_code = 503
    default_detail = 'Uma dependência necessária ainda não foi configurada.'


class ReservationNotFoundException(GiroException):
    code = 'NOT_FOUND'
    status_code = 404
    default_detail = 'Reserva não encontrada.'
