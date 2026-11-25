import { apiRequest } from '../../../shared/api/client'

export interface RentalPickupResult {
  id: number
  status: string
  picked_up_at: string
}

export interface RentalReturnResult {
  id: number
  status: string
  returned_at: string
  late_day_count: number
  late_charge_amount: string
  inter_branch_charge_amount: string
  damage_charge_amount: string
  balance_due: string
}

export interface RentalFinalizeResult {
  id: number
  status: string
  finalized_at: string
}

export interface RentalSummary {
  id: number
  customer_id: number
  status: string
  pickup_branch_id: number
  return_branch_id: number
  actual_return_branch_id: number | null
  starts_at: string
  expected_return_at: string
}

export interface OverdueAlert {
  rental_id: number
  affected_reservation_id: number
  equivalent_vehicle_ids: number[]
}

export interface RentalList {
  count: number
  next: string | null
  results: RentalSummary[]
  overdue_alerts: OverdueAlert[]
}

export async function pickUpRental(
  rentalId: string,
  inspectionId: number,
): Promise<RentalPickupResult> {
  return apiRequest(`/rentals/${encodeURIComponent(rentalId)}/pick-up`, {
    method: 'POST',
    body: JSON.stringify({ inspection_id: inspectionId }),
  })
}

export async function returnRental(
  rentalId: string,
  inspectionId: number,
  returnBranchId: number,
): Promise<RentalReturnResult> {
  return apiRequest(`/rentals/${encodeURIComponent(rentalId)}/return`, {
    method: 'POST',
    body: JSON.stringify({
      inspection_id: inspectionId,
      return_branch_id: returnBranchId,
    }),
  })
}

export async function finalizeRental(
  rentalId: string,
): Promise<RentalFinalizeResult> {
  return apiRequest(`/rentals/${encodeURIComponent(rentalId)}/finalize`, {
    method: 'POST',
  })
}

export async function listRentals(
  filters: Record<string, string> = {},
): Promise<RentalList> {
  const query = new URLSearchParams(filters)
  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return apiRequest(`/rentals${suffix}`)
}
