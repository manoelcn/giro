import { apiRequest } from '../../../shared/api/client'

export type VehicleType = 'VEHICLE' | 'CAR' | 'MOTORCYCLE' | 'UTILITYVEHICLE'
export type VehicleStatus = 'AVAILABLE' | 'RESERVED' | 'RENTED' | 'MAINTENANCE'
export type InspectionType = 'EXIT' | 'ENTRY'

export interface FleetList<T> {
  count: number
  next: string | null
  results: T[]
}

export interface Branch {
  [key: string]: unknown
  id: number
  name: string
  address: string
  city: string
  state: string
}

export interface BranchInput {
  name: string
  address: string
  city: string
  state: string
}

export interface Vehicle {
  [key: string]: unknown
  id: number
  plate: string
  model: string
  year: number
  mileage: number
  status: VehicleStatus
  daily_rate: string
  deposit_amount: string
  required_license_category: string
  minimum_driver_age: number
  branch: number
  branch_name: string
  vehicle_type: VehicleType
  last_maintenance_mileage: number
  maintenance_interval_km: number
  doors: number | null
  trunk_capacity_liters: number | null
  displacement_cc: number | null
  helmet_included: boolean | null
  load_capacity_kg: number | null
}

export interface VehicleInput {
  vehicle_type: VehicleType
  plate: string
  model: string
  year: number
  mileage: number
  status?: VehicleStatus
  daily_rate: string
  deposit_amount: string
  required_license_category: string
  minimum_driver_age: number
  branch: number
  maintenance_interval_km: number
  doors?: number
  trunk_capacity_liters?: number
  displacement_cc?: number
  helmet_included?: boolean
  load_capacity_kg?: number
}

export interface Inspection {
  [key: string]: unknown
  id: number
  rental_id: number
  inspection_type: InspectionType
  mileage: number
  damages: string
  damage_description: string
  has_damage: boolean
  created_at: string
}

export interface InspectionInput {
  rental_id: number
  inspection_type: InspectionType
  mileage: number
  damages: string
  damage_description: string
}

export interface MaintenanceRecord {
  [key: string]: unknown
  id: number
  vehicle: number
  vehicle_plate: string
  vehicle_model: string
  reason: string
  mileage: number
  started_at: string
  completed_at: string | null
}

export async function listVehicles(): Promise<FleetList<Vehicle>> {
  return apiRequest('/fleet/vehicles')
}

export async function saveVehicle(input: VehicleInput, id?: number): Promise<Vehicle> {
  return apiRequest(id ? `/fleet/vehicles/${id}` : '/fleet/vehicles', {
    method: id ? 'PATCH' : 'POST',
    body: JSON.stringify(input),
  })
}

export async function deleteVehicle(id: number): Promise<void> {
  return apiRequest(`/fleet/vehicles/${id}`, { method: 'DELETE' })
}

export async function listBranches(): Promise<FleetList<Branch>> {
  return apiRequest('/fleet/branches')
}

export async function saveBranch(input: BranchInput, id?: number): Promise<Branch> {
  return apiRequest(id ? `/fleet/branches/${id}` : '/fleet/branches', {
    method: id ? 'PATCH' : 'POST',
    body: JSON.stringify(input),
  })
}

export async function deleteBranch(id: number): Promise<void> {
  return apiRequest(`/fleet/branches/${id}`, { method: 'DELETE' })
}

export async function findAvailableVehicles(
  startsAt: string,
  expectedReturnAt: string,
): Promise<FleetList<Vehicle>> {
  const query = new URLSearchParams({
    starts_at: startsAt,
    expected_return_at: expectedReturnAt,
  })
  return apiRequest(`/fleet/availability?${query.toString()}`)
}

export async function listInspections(rentalId?: string): Promise<FleetList<Inspection>> {
  const query = new URLSearchParams()
  if (rentalId) query.set('rental_id', rentalId)
  const suffix = query.size ? `?${query.toString()}` : ''
  return apiRequest(`/fleet/inspections${suffix}`)
}

export async function registerInspection(input: InspectionInput): Promise<Inspection> {
  return apiRequest('/fleet/inspections', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function listMaintenance(activeOnly = false): Promise<FleetList<MaintenanceRecord>> {
  const suffix = activeOnly ? '?active=true' : ''
  return apiRequest(`/fleet/maintenance${suffix}`)
}

export async function startMaintenance(input: {
  vehicle_id: number
  reason: string
  mileage?: number
}): Promise<MaintenanceRecord> {
  return apiRequest('/fleet/maintenance', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function releaseMaintenance(id: number): Promise<MaintenanceRecord> {
  return apiRequest(`/fleet/maintenance/${id}/release`, { method: 'POST' })
}