import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  AvailabilityPage,
  InspectionPage,
  MaintenancePage,
  VehicleManagementPage,
} from '../FleetPages'
import {
  findAvailableVehicles,
  listBranches,
  listInspections,
  listMaintenance,
  listVehicles,
  registerInspection,
  releaseMaintenance,
  saveVehicle,
} from '../api/fleet'

vi.mock('../api/fleet', () => ({
  deleteBranch: vi.fn(),
  deleteVehicle: vi.fn(),
  findAvailableVehicles: vi.fn(),
  listBranches: vi.fn(),
  listInspections: vi.fn(),
  listMaintenance: vi.fn(),
  listVehicles: vi.fn(),
  registerInspection: vi.fn(),
  releaseMaintenance: vi.fn(),
  saveBranch: vi.fn(),
  saveVehicle: vi.fn(),
  startMaintenance: vi.fn(),
}))

const branch = {
  id: 1,
  name: 'Centro',
  address: 'Rua Central, 1',
  city: 'São Paulo',
  state: 'SP',
}

const vehicle = {
  id: 5,
  plate: 'ABC1D23',
  model: 'Sedan',
  year: 2025,
  mileage: 1200,
  status: 'AVAILABLE' as const,
  daily_rate: '120.00',
  deposit_amount: '300.00',
  required_license_category: 'B',
  minimum_driver_age: 21,
  branch: 1,
  branch_name: 'Centro',
  vehicle_type: 'CAR' as const,
  last_maintenance_mileage: 0,
  maintenance_interval_km: 10000,
  doors: 4,
  trunk_capacity_liters: 300,
  displacement_cc: null,
  helmet_included: null,
  load_capacity_kg: null,
}

const emptyList = { count: 0, next: null, results: [] }

function renderInApp(ui: React.ReactNode, initialEntry = '/') {
  return render(<MemoryRouter initialEntries={[initialEntry]}>{ui}</MemoryRouter>)
}

describe('fleet pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listVehicles).mockResolvedValue(emptyList)
    vi.mocked(listBranches).mockResolvedValue({ count: 1, next: null, results: [branch] })
    vi.mocked(listInspections).mockResolvedValue(emptyList)
    vi.mocked(listMaintenance).mockResolvedValue(emptyList)
  })

  it('creates a vehicle from the fleet form', async () => {
    vi.mocked(saveVehicle).mockResolvedValue(vehicle)
    renderInApp(<VehicleManagementPage />)

    expect(await screen.findByText('Frota cadastrada (0)')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Placa'), { target: { value: 'ABC1D23' } })
    fireEvent.change(screen.getByLabelText('Modelo'), { target: { value: 'Sedan' } })
    fireEvent.change(screen.getByLabelText('Filial'), { target: { value: '1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cadastrar veículo' }))

    await waitFor(() => expect(saveVehicle).toHaveBeenCalledWith(
      expect.objectContaining({ plate: 'ABC1D23', vehicle_type: 'CAR', branch: 1 }),
      undefined,
    ))
    expect(await screen.findByText('Veículo cadastrado.')).toBeInTheDocument()
  })

  it('shows vehicles available for the selected period', async () => {
    vi.mocked(findAvailableVehicles).mockResolvedValue({
      count: 1,
      next: null,
      results: [vehicle],
    })
    renderInApp(<AvailabilityPage />)
    fireEvent.change(screen.getByLabelText('Retirada'), {
      target: { value: '2027-01-10T09:00' },
    })
    fireEvent.change(screen.getByLabelText('Devolução prevista'), {
      target: { value: '2027-01-12T09:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Consultar veículos' }))

    expect(await screen.findByText('ABC1D23')).toBeInTheDocument()
    expect(findAvailableVehicles).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
    )
  })

  it('prefills the inspection form from the rental query and registers it', async () => {
    vi.mocked(registerInspection).mockResolvedValue({
      id: 10,
      rental_id: 8,
      inspection_type: 'EXIT',
      mileage: 1250,
      damages: '0.00',
      damage_description: '',
      has_damage: false,
      created_at: '2026-11-26T12:00:00Z',
    })
    renderInApp(<InspectionPage />, '/fleet/inspections?rentalId=8&type=EXIT')
    fireEvent.change(screen.getByLabelText('Quilometragem (km)'), {
      target: { value: '1250' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar vistoria' }))

    await waitFor(() => expect(registerInspection).toHaveBeenCalledWith({
      rental_id: 8,
      inspection_type: 'EXIT',
      mileage: 1250,
      damages: '0.00',
      damage_description: '',
    }))
    expect(await screen.findByText('Vistoria registrada.')).toBeInTheDocument()
  })

  it('releases a maintenance record', async () => {
    vi.mocked(listMaintenance).mockResolvedValue({
      count: 1,
      next: null,
      results: [{
        id: 9,
        vehicle: 5,
        vehicle_plate: 'ABC1D23',
        vehicle_model: 'Sedan',
        reason: 'Revisão programada',
        mileage: 1200,
        started_at: '2026-11-26T12:00:00Z',
        completed_at: null,
      }],
    })
    vi.mocked(releaseMaintenance).mockResolvedValue({
      id: 9,
      vehicle: 5,
      vehicle_plate: 'ABC1D23',
      vehicle_model: 'Sedan',
      reason: 'Revisão programada',
      mileage: 1200,
      started_at: '2026-11-26T12:00:00Z',
      completed_at: '2026-11-26T13:00:00Z',
    })
    renderInApp(<MaintenancePage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Liberar veículo' }))

    await waitFor(() => expect(releaseMaintenance).toHaveBeenCalledWith(9))
    expect(await screen.findByText('Veículo ABC1D23 liberado.')).toBeInTheDocument()
  })
})