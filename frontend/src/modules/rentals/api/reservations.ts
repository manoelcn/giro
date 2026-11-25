import { apiRequest } from '../../../shared/api/client'

export interface ReservationInput {
  customer_id: number
  vehicle_id: number
  starts_at: string
  expected_return_at: string
  pickup_branch_id: number
  return_branch_id: number
  insurance_id: number | null
}

export interface ReservationQuote {
  daily_rate: string
  first_day_amount: string
  quoted_total: string
  currency: string
}

export interface Reservation {
  id: number
  rental_id: number | null
  rental_status?: string | null
  status: string
  starts_at: string
  expected_return_at: string
  quoted_total: string
}

export interface ReservationList {
  count: number
  next: string | null
  results: Reservation[]
}

export interface CancellationCharge {
  type: 'CANCELLATION'
  amount: string
  status: 'PENDING'
}

export interface CancellationQuote {
  cancellation_charge: CancellationCharge | null
}

export interface CancellationResult {
  id: number
  status: 'CANCELED'
  cancellation_charge: CancellationCharge | null
}

export async function quoteReservation(
  input: ReservationInput,
): Promise<ReservationQuote> {
  return apiRequest('/reservations/quote', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function createReservation(
  input: ReservationInput & { accepted_total: string },
): Promise<Reservation> {
  return apiRequest('/reservations', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function listReservations(
  filters: Record<string, string> = {},
): Promise<ReservationList> {
  const query = new URLSearchParams(filters)
  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return apiRequest(`/reservations${suffix}`)
}

export async function getReservation(id: string): Promise<Reservation> {
  return apiRequest(`/reservations/${encodeURIComponent(id)}`)
}

export async function getCancellationQuote(
  reservationId: string,
): Promise<CancellationQuote> {
  return apiRequest(`/reservations/${encodeURIComponent(reservationId)}/cancel`)
}

export async function cancelReservation(
  reservationId: string,
): Promise<CancellationResult> {
  return apiRequest(`/reservations/${encodeURIComponent(reservationId)}/cancel`, {
    method: 'POST',
  })
}
