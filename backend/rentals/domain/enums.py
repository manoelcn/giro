from enum import StrEnum


class ReservationStatus(StrEnum):
    CONFIRMED = 'CONFIRMED'
    CANCELED = 'CANCELED'
    FULFILLED = 'FULFILLED'


class RentalStatus(StrEnum):
    RESERVED = 'RESERVED'
    PICKED_UP = 'PICKED_UP'
    OVERDUE = 'OVERDUE'
    RETURNED = 'RETURNED'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'
