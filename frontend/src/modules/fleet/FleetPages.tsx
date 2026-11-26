import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { NavLink, useSearchParams } from 'react-router-dom'
import { Badge } from '@astryxdesign/core/Badge'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Table, type TableColumn } from '@astryxdesign/core/Table'
import { Text } from '@astryxdesign/core/Text'
import { VStack } from '@astryxdesign/core/VStack'

import {
  deleteBranch,
  deleteVehicle,
  findAvailableVehicles,
  listBranches,
  listInspections,
  listMaintenance,
  listVehicles,
  registerInspection,
  releaseMaintenance,
  saveBranch,
  saveVehicle,
  startMaintenance,
  type Branch,
  type BranchInput,
  type Inspection,
  type InspectionType,
  type MaintenanceRecord,
  type Vehicle,
  type VehicleInput,
  type VehicleStatus,
  type VehicleType,
} from './api/fleet'
import { Feedback, Page } from '../../shared/ui/Page'

const fleetLinks = [
  { to: '/fleet/vehicles', label: 'Veículos' },
  { to: '/fleet/branches', label: 'Filiais' },
  { to: '/fleet/availability', label: 'Disponibilidade' },
  { to: '/fleet/inspections', label: 'Vistorias' },
  { to: '/fleet/maintenance', label: 'Manutenção' },
]

const statusLabels: Record<VehicleStatus, string> = {
  AVAILABLE: 'Disponível',
  RESERVED: 'Reservado',
  RENTED: 'Locado',
  MAINTENANCE: 'Em manutenção',
}

const statusVariants: Record<VehicleStatus, 'success' | 'info' | 'warning' | 'neutral'> = {
  AVAILABLE: 'success',
  RESERVED: 'info',
  RENTED: 'warning',
  MAINTENANCE: 'neutral',
}

const vehicleTypeLabels: Record<VehicleType, string> = {
  VEHICLE: 'Veículo',
  CAR: 'Carro',
  MOTORCYCLE: 'Motocicleta',
  UTILITYVEHICLE: 'Utilitário',
}

function FleetLayout({
  title,
  description,
  children,
}: {
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <Page description={description} title={title}>
      <HStack as="nav" aria-label="Seções da frota" className="fleet-nav" gap={3} wrap="wrap">
        {fleetLinks.map((item) => (
          <NavLink
            className={({ isActive }) => `fleet-nav-link${isActive ? ' is-active' : ''}`}
            key={item.to}
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
      </HStack>
      {children}
    </Page>
  )
}

function VehicleTable({
  vehicles,
  onEdit,
  onDelete,
}: {
  vehicles: Vehicle[]
  onEdit?: (vehicle: Vehicle) => void
  onDelete?: (vehicle: Vehicle) => void
}) {
  const columns: TableColumn<Vehicle>[] = [
    { key: 'plate', header: 'Placa' },
    {
      key: 'model',
      header: 'Veículo',
      renderCell: (vehicle) => `${vehicle.model} (${vehicle.year})`,
    },
    {
      key: 'vehicle_type',
      header: 'Tipo',
      renderCell: (vehicle) => vehicleTypeLabels[vehicle.vehicle_type],
    },
    { key: 'branch_name', header: 'Filial' },
    {
      key: 'mileage',
      header: 'Quilometragem',
      renderCell: (vehicle) => `${vehicle.mileage.toLocaleString('pt-BR')} km`,
    },
    {
      key: 'status',
      header: 'Situação',
      renderCell: (vehicle) => (
        <Badge label={statusLabels[vehicle.status]} variant={statusVariants[vehicle.status]} />
      ),
    },
    ...(onEdit || onDelete
      ? [
          {
            key: 'id' as const,
            header: 'Ações',
            renderCell: (vehicle: Vehicle) => (
              <HStack gap={1} wrap="wrap">
                {onEdit && (
                  <Button
                    label="Editar"
                    onClick={() => onEdit(vehicle)}
                    size="sm"
                    variant="secondary"
                  />
                )}
                {onDelete && (
                  <Button
                    label="Excluir"
                    onClick={() => onDelete(vehicle)}
                    size="sm"
                    variant="destructive"
                  />
                )}
              </HStack>
            ),
          },
        ]
      : []),
  ]

  return (
    <section className="fleet-table-wrap" aria-label="Veículos">
      <Table
        columns={columns}
        data={vehicles}
        emptyState={<Text as="p">Nenhum veículo corresponde à consulta.</Text>}
        hasHover
        idKey="id"
      />
    </section>
  )
}

function loadError(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

type VehicleDraft = {
  vehicle_type: VehicleType
  plate: string
  model: string
  year: string
  mileage: string
  daily_rate: string
  deposit_amount: string
  required_license_category: string
  minimum_driver_age: string
  branch: string
  maintenance_interval_km: string
  doors: string
  trunk_capacity_liters: string
  displacement_cc: string
  helmet_included: string
  load_capacity_kg: string
}

function emptyVehicleDraft(): VehicleDraft {
  return {
    vehicle_type: 'CAR',
    plate: '',
    model: '',
    year: String(new Date().getFullYear()),
    mileage: '0',
    daily_rate: '120.00',
    deposit_amount: '300.00',
    required_license_category: 'B',
    minimum_driver_age: '21',
    branch: '',
    maintenance_interval_km: '10000',
    doors: '4',
    trunk_capacity_liters: '300',
    displacement_cc: '150',
    helmet_included: 'true',
    load_capacity_kg: '500',
  }
}

function draftFromVehicle(vehicle: Vehicle): VehicleDraft {
  return {
    vehicle_type: vehicle.vehicle_type,
    plate: vehicle.plate,
    model: vehicle.model,
    year: String(vehicle.year),
    mileage: String(vehicle.mileage),
    daily_rate: vehicle.daily_rate,
    deposit_amount: vehicle.deposit_amount,
    required_license_category: vehicle.required_license_category,
    minimum_driver_age: String(vehicle.minimum_driver_age),
    branch: String(vehicle.branch),
    maintenance_interval_km: String(vehicle.maintenance_interval_km),
    doors: String(vehicle.doors ?? 4),
    trunk_capacity_liters: String(vehicle.trunk_capacity_liters ?? 300),
    displacement_cc: String(vehicle.displacement_cc ?? 150),
    helmet_included: String(vehicle.helmet_included ?? true),
    load_capacity_kg: String(vehicle.load_capacity_kg ?? 500),
  }
}

function vehicleInput(draft: VehicleDraft): VehicleInput {
  const input: VehicleInput = {
    vehicle_type: draft.vehicle_type,
    plate: draft.plate.trim().toUpperCase(),
    model: draft.model.trim(),
    year: Number(draft.year),
    mileage: Number(draft.mileage),
    daily_rate: draft.daily_rate,
    deposit_amount: draft.deposit_amount,
    required_license_category: draft.required_license_category,
    minimum_driver_age: Number(draft.minimum_driver_age),
    branch: Number(draft.branch),
    maintenance_interval_km: Number(draft.maintenance_interval_km),
  }
  if (draft.vehicle_type === 'CAR') {
    input.doors = Number(draft.doors)
    input.trunk_capacity_liters = Number(draft.trunk_capacity_liters)
  } else if (draft.vehicle_type === 'MOTORCYCLE') {
    input.displacement_cc = Number(draft.displacement_cc)
    input.helmet_included = draft.helmet_included === 'true'
  } else if (draft.vehicle_type === 'UTILITYVEHICLE') {
    input.load_capacity_kg = Number(draft.load_capacity_kg)
  }
  return input
}

export function VehicleManagementPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [draft, setDraft] = useState<VehicleDraft>(emptyVehicleDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function refresh() {
    const [vehicleList, branchList] = await Promise.all([listVehicles(), listBranches()])
    setVehicles(vehicleList.results)
    setBranches(branchList.results)
  }

  useEffect(() => {
    let active = true
    Promise.all([listVehicles(), listBranches()])
      .then(([vehicleList, branchList]) => {
        if (active) {
          setVehicles(vehicleList.results)
          setBranches(branchList.results)
        }
      })
      .catch((requestError: unknown) => {
        if (active) setError(loadError(requestError, 'Não foi possível carregar a frota.'))
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await saveVehicle(vehicleInput(draft), editingId ?? undefined)
      await refresh()
      setDraft(emptyVehicleDraft())
      setEditingId(null)
      setMessage(editingId ? 'Veículo atualizado.' : 'Veículo cadastrado.')
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível salvar o veículo.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(vehicle: Vehicle) {
    if (!window.confirm(`Excluir o veículo ${vehicle.plate}?`)) return
    setError('')
    setMessage('')
    try {
      await deleteVehicle(vehicle.id)
      await refresh()
      setMessage(`Veículo ${vehicle.plate} excluído.`)
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível excluir o veículo.'))
    }
  }

  return (
    <FleetLayout
      description="Cadastre veículos, mantenha seus dados e consulte a situação de cada unidade."
      title="Veículos"
    >
      <VStack as="section" aria-label={editingId ? 'Editar veículo' : 'Cadastrar veículo'} gap={3}>
        <Heading level={2}>{editingId ? `Editar veículo #${editingId}` : 'Novo veículo'}</Heading>
        <form onSubmit={handleSubmit}>
          <VStack gap={3}>
            <Grid columns={{ minWidth: 220, max: 3 }} gap={3}>
              <Field inputID="vehicle-type" label="Tipo de veículo">
                <select
                  className="native-control"
                  id="vehicle-type"
                  value={draft.vehicle_type}
                  onChange={(event) => setDraft({ ...draft, vehicle_type: event.target.value as VehicleType })}
                >
                  {Object.entries(vehicleTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </Field>
              <Field inputID="vehicle-plate" label="Placa">
                <input className="native-control" id="vehicle-plate" maxLength={8} required value={draft.plate} onChange={(event) => setDraft({ ...draft, plate: event.target.value })} />
              </Field>
              <Field inputID="vehicle-model" label="Modelo">
                <input className="native-control" id="vehicle-model" maxLength={100} required value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} />
              </Field>
              <Field inputID="vehicle-year" label="Ano">
                <input className="native-control" id="vehicle-year" min="1900" required type="number" value={draft.year} onChange={(event) => setDraft({ ...draft, year: event.target.value })} />
              </Field>
              <Field inputID="vehicle-mileage" label="Quilometragem (km)">
                <input className="native-control" id="vehicle-mileage" min="0" required type="number" value={draft.mileage} onChange={(event) => setDraft({ ...draft, mileage: event.target.value })} />
              </Field>
              <Field inputID="vehicle-branch" label="Filial">
                <select className="native-control" id="vehicle-branch" required value={draft.branch} onChange={(event) => setDraft({ ...draft, branch: event.target.value })}>
                  <option value="">Selecione uma filial</option>
                  {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name} · {branch.city}</option>)}
                </select>
              </Field>
              <Field inputID="vehicle-rate" label="Diária (R$)">
                <input className="native-control" id="vehicle-rate" min="0" required step="0.01" type="number" value={draft.daily_rate} onChange={(event) => setDraft({ ...draft, daily_rate: event.target.value })} />
              </Field>
              <Field inputID="vehicle-deposit" label="Caução (R$)">
                <input className="native-control" id="vehicle-deposit" min="0" required step="0.01" type="number" value={draft.deposit_amount} onChange={(event) => setDraft({ ...draft, deposit_amount: event.target.value })} />
              </Field>
              <Field inputID="vehicle-license" label="Categoria de CNH">
                <select className="native-control" id="vehicle-license" value={draft.required_license_category} onChange={(event) => setDraft({ ...draft, required_license_category: event.target.value })}>
                  <option value="A">A</option><option value="B">B</option><option value="C">C</option>
                </select>
              </Field>
              <Field inputID="vehicle-age" label="Idade mínima">
                <input className="native-control" id="vehicle-age" min="18" required type="number" value={draft.minimum_driver_age} onChange={(event) => setDraft({ ...draft, minimum_driver_age: event.target.value })} />
              </Field>
              <Field inputID="vehicle-service-interval" label="Intervalo de revisão (km)">
                <input className="native-control" id="vehicle-service-interval" min="1" required type="number" value={draft.maintenance_interval_km} onChange={(event) => setDraft({ ...draft, maintenance_interval_km: event.target.value })} />
              </Field>
              {draft.vehicle_type === 'CAR' && <>
                <Field inputID="vehicle-doors" label="Portas">
                  <input className="native-control" id="vehicle-doors" min="1" required type="number" value={draft.doors} onChange={(event) => setDraft({ ...draft, doors: event.target.value })} />
                </Field>
                <Field inputID="vehicle-trunk" label="Porta-malas (L)">
                  <input className="native-control" id="vehicle-trunk" min="0" required type="number" value={draft.trunk_capacity_liters} onChange={(event) => setDraft({ ...draft, trunk_capacity_liters: event.target.value })} />
                </Field>
              </>}
              {draft.vehicle_type === 'MOTORCYCLE' && <>
                <Field inputID="vehicle-engine" label="Cilindrada (cc)">
                  <input className="native-control" id="vehicle-engine" min="1" required type="number" value={draft.displacement_cc} onChange={(event) => setDraft({ ...draft, displacement_cc: event.target.value })} />
                </Field>
                <Field inputID="vehicle-helmet" label="Capacete incluso">
                  <select className="native-control" id="vehicle-helmet" value={draft.helmet_included} onChange={(event) => setDraft({ ...draft, helmet_included: event.target.value })}>
                    <option value="true">Sim</option><option value="false">Não</option>
                  </select>
                </Field>
              </>}
              {draft.vehicle_type === 'UTILITYVEHICLE' && <Field inputID="vehicle-load" label="Capacidade de carga (kg)">
                <input className="native-control" id="vehicle-load" min="1" required type="number" value={draft.load_capacity_kg} onChange={(event) => setDraft({ ...draft, load_capacity_kg: event.target.value })} />
              </Field>}
            </Grid>
            <HStack className="form-actions" gap={2}>
              {editingId && <Button label="Cancelar edição" onClick={() => { setEditingId(null); setDraft(emptyVehicleDraft()) }} variant="secondary" />}
              <Button isDisabled={isSubmitting || branches.length === 0} label={isSubmitting ? 'Salvando...' : editingId ? 'Salvar veículo' : 'Cadastrar veículo'} type="submit" />
            </HStack>
          </VStack>
        </form>
      </VStack>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
      {isLoading ? <Text as="p" role="status">Carregando veículos...</Text> : (
        <VStack as="section" aria-label="Frota cadastrada" gap={2}>
          <Heading level={2}>Frota cadastrada ({vehicles.length})</Heading>
          <VehicleTable vehicles={vehicles} onDelete={handleDelete} onEdit={(vehicle) => { setEditingId(vehicle.id); setDraft(draftFromVehicle(vehicle)); setError(''); setMessage('') }} />
        </VStack>
      )}
    </FleetLayout>
  )
}

type BranchDraft = BranchInput

export function BranchManagementPage() {
  const [branches, setBranches] = useState<Branch[]>([])
  const [draft, setDraft] = useState<BranchDraft>({ name: '', address: '', city: '', state: '' })
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function refresh() {
    setBranches((await listBranches()).results)
  }

  useEffect(() => {
    let active = true
    listBranches()
      .then((result) => { if (active) setBranches(result.results) })
      .catch((requestError: unknown) => { if (active) setError(loadError(requestError, 'Não foi possível carregar as filiais.')) })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await saveBranch({ ...draft, state: draft.state.toUpperCase() }, editingId ?? undefined)
      await refresh()
      setDraft({ name: '', address: '', city: '', state: '' })
      setEditingId(null)
      setMessage(editingId ? 'Filial atualizada.' : 'Filial cadastrada.')
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível salvar a filial.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(branch: Branch) {
    if (!window.confirm(`Excluir a filial ${branch.name}?`)) return
    setError('')
    setMessage('')
    try {
      await deleteBranch(branch.id)
      await refresh()
      setMessage(`Filial ${branch.name} excluída.`)
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível excluir a filial.'))
    }
  }

  const columns: TableColumn<Branch>[] = [
    { key: 'name', header: 'Nome' },
    { key: 'address', header: 'Endereço' },
    { key: 'city', header: 'Cidade' },
    { key: 'state', header: 'UF' },
    {
      key: 'id',
      header: 'Ações',
      renderCell: (branch) => <HStack gap={1} wrap="wrap">
        <Button label="Editar" onClick={() => { setEditingId(branch.id); setDraft({ name: branch.name, address: branch.address, city: branch.city, state: branch.state }); setError(''); setMessage('') }} size="sm" variant="secondary" />
        <Button label="Excluir" onClick={() => handleDelete(branch)} size="sm" variant="destructive" />
      </HStack>,
    },
  ]

  return (
    <FleetLayout description="Gerencie os pontos de retirada e devolução da locadora." title="Filiais">
      <VStack as="section" aria-label={editingId ? 'Editar filial' : 'Cadastrar filial'} gap={3}>
        <Heading level={2}>{editingId ? `Editar filial #${editingId}` : 'Nova filial'}</Heading>
        <form onSubmit={handleSubmit}>
          <VStack gap={3}>
            <Grid columns={{ minWidth: 220, max: 2 }} gap={3}>
              <Field inputID="branch-name" label="Nome"><input className="native-control" id="branch-name" maxLength={100} required value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></Field>
              <Field inputID="branch-address" label="Endereço"><input className="native-control" id="branch-address" maxLength={255} required value={draft.address} onChange={(event) => setDraft({ ...draft, address: event.target.value })} /></Field>
              <Field inputID="branch-city" label="Cidade"><input className="native-control" id="branch-city" maxLength={100} required value={draft.city} onChange={(event) => setDraft({ ...draft, city: event.target.value })} /></Field>
              <Field inputID="branch-state" label="UF"><input className="native-control" id="branch-state" maxLength={2} minLength={2} required value={draft.state} onChange={(event) => setDraft({ ...draft, state: event.target.value.toUpperCase() })} /></Field>
            </Grid>
            <HStack className="form-actions" gap={2}>
              {editingId && <Button label="Cancelar edição" onClick={() => { setEditingId(null); setDraft({ name: '', address: '', city: '', state: '' }) }} variant="secondary" />}
              <Button isDisabled={isSubmitting} label={isSubmitting ? 'Salvando...' : editingId ? 'Salvar filial' : 'Cadastrar filial'} type="submit" />
            </HStack>
          </VStack>
        </form>
      </VStack>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
      {isLoading ? <Text as="p" role="status">Carregando filiais...</Text> : (
        <VStack as="section" aria-label="Filiais cadastradas" gap={2}>
          <Heading level={2}>Filiais cadastradas ({branches.length})</Heading>
          <section className="fleet-table-wrap" aria-label="Tabela de filiais">
            <Table columns={columns} data={branches} emptyState={<Text as="p">Nenhuma filial cadastrada.</Text>} hasHover idKey="id" />
          </section>
        </VStack>
      )}
    </FleetLayout>
  )
}

export function AvailabilityPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [startsAt, setStartsAt] = useState('')
  const [expectedReturnAt, setExpectedReturnAt] = useState('')
  const [error, setError] = useState('')
  const [hasSearched, setHasSearched] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const result = await findAvailableVehicles(
        new Date(startsAt).toISOString(),
        new Date(expectedReturnAt).toISOString(),
      )
      setVehicles(result.results)
      setHasSearched(true)
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível consultar a disponibilidade.'))
      setHasSearched(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <FleetLayout description="Encontre veículos livres entre a retirada e a devolução previstas." title="Disponibilidade">
      <form onSubmit={handleSubmit}>
        <VStack gap={3}>
          <Grid columns={{ minWidth: 240, max: 2 }} gap={3}>
            <Field inputID="availability-start" label="Retirada">
              <input className="native-control" id="availability-start" required type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} />
            </Field>
            <Field inputID="availability-return" label="Devolução prevista">
              <input className="native-control" id="availability-return" required type="datetime-local" value={expectedReturnAt} onChange={(event) => setExpectedReturnAt(event.target.value)} />
            </Field>
          </Grid>
          <HStack className="form-actions">
            <Button isDisabled={isSubmitting} label={isSubmitting ? 'Consultando...' : 'Consultar veículos'} type="submit" />
          </HStack>
        </VStack>
      </form>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {hasSearched && <VStack as="section" aria-label="Resultado da disponibilidade" gap={2}>
        <Heading level={2}>{vehicles.length} veículo(s) disponível(is)</Heading>
        <VehicleTable vehicles={vehicles} />
      </VStack>}
    </FleetLayout>
  )
}

const inspectionLabels: Record<InspectionType, string> = {
  EXIT: 'Saída',
  ENTRY: 'Entrada',
}

export function InspectionPage() {
  const [searchParams] = useSearchParams()
  const [rentalId, setRentalId] = useState(searchParams.get('rentalId') ?? '')
  const [inspectionType, setInspectionType] = useState<InspectionType>(
    searchParams.get('type') === 'ENTRY' ? 'ENTRY' : 'EXIT',
  )
  const [mileage, setMileage] = useState('')
  const [damages, setDamages] = useState('0.00')
  const [damageDescription, setDamageDescription] = useState('')
  const [inspections, setInspections] = useState<Inspection[]>([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function refresh() {
    setInspections((await listInspections()).results)
  }

  useEffect(() => {
    let active = true
    listInspections()
      .then((result) => { if (active) setInspections(result.results) })
      .catch((requestError: unknown) => { if (active) setError(loadError(requestError, 'Não foi possível carregar as vistorias.')) })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await registerInspection({
        rental_id: Number(rentalId),
        inspection_type: inspectionType,
        mileage: Number(mileage),
        damages,
        damage_description: damageDescription,
      })
      await refresh()
      setMileage('')
      setDamages('0.00')
      setDamageDescription('')
      setMessage('Vistoria registrada.')
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível registrar a vistoria.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const columns: TableColumn<Inspection>[] = [
    { key: 'id', header: 'Nº' },
    { key: 'rental_id', header: 'Locação' },
    { key: 'inspection_type', header: 'Etapa', renderCell: (inspection) => inspectionLabels[inspection.inspection_type] },
    { key: 'mileage', header: 'Quilometragem', renderCell: (inspection) => `${inspection.mileage.toLocaleString('pt-BR')} km` },
    { key: 'damages', header: 'Avarias (R$)' },
    { key: 'damage_description', header: 'Descrição' },
    { key: 'has_damage', header: 'Resultado', renderCell: (inspection) => <Badge label={inspection.has_damage ? 'Com avaria' : 'Sem avaria'} variant={inspection.has_damage ? 'warning' : 'success'} /> },
    { key: 'created_at', header: 'Registrada em', renderCell: (inspection) => new Date(inspection.created_at).toLocaleString('pt-BR') },
  ]

  return (
    <FleetLayout description="Registre as condições do veículo na retirada ou devolução da locação." title="Vistorias">
      <VStack as="section" aria-label="Registrar vistoria" gap={3}>
        <Heading level={2}>Nova vistoria</Heading>
        <form onSubmit={handleSubmit}>
          <VStack gap={3}>
            <Grid columns={{ minWidth: 220, max: 3 }} gap={3}>
              <Field inputID="inspection-rental" label="Número da locação">
                <input className="native-control" id="inspection-rental" min="1" required type="number" value={rentalId} onChange={(event) => setRentalId(event.target.value)} />
              </Field>
              <Field inputID="inspection-type" label="Etapa">
                <select className="native-control" id="inspection-type" value={inspectionType} onChange={(event) => setInspectionType(event.target.value as InspectionType)}>
                  <option value="EXIT">Saída</option><option value="ENTRY">Entrada</option>
                </select>
              </Field>
              <Field inputID="inspection-mileage" label="Quilometragem (km)">
                <input className="native-control" id="inspection-mileage" min="0" required type="number" value={mileage} onChange={(event) => setMileage(event.target.value)} />
              </Field>
              <Field inputID="inspection-damages" label="Valor das avarias (R$)">
                <input className="native-control" id="inspection-damages" min="0" required step="0.01" type="number" value={damages} onChange={(event) => setDamages(event.target.value)} />
              </Field>
              <Field inputID="inspection-description" label="Descrição da avaria" isOptional>
                <input className="native-control" id="inspection-description" maxLength={500} value={damageDescription} onChange={(event) => setDamageDescription(event.target.value)} />
              </Field>
            </Grid>
            <HStack className="form-actions">
              <Button isDisabled={isSubmitting} label={isSubmitting ? 'Registrando...' : 'Registrar vistoria'} type="submit" />
            </HStack>
          </VStack>
        </form>
      </VStack>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
      {isLoading ? <Text as="p" role="status">Carregando vistorias...</Text> : (
        <VStack as="section" aria-label="Histórico de vistorias" gap={2}>
          <Heading level={2}>Histórico ({inspections.length})</Heading>
          <section className="fleet-table-wrap" aria-label="Tabela de vistorias">
            <Table columns={columns} data={inspections} emptyState={<Text as="p">Nenhuma vistoria registrada.</Text>} hasHover idKey="id" />
          </section>
        </VStack>
      )}
    </FleetLayout>
  )
}

export function MaintenancePage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [records, setRecords] = useState<MaintenanceRecord[]>([])
  const [vehicleId, setVehicleId] = useState('')
  const [reason, setReason] = useState('')
  const [mileage, setMileage] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function refresh() {
    setRecords((await listMaintenance()).results)
  }

  useEffect(() => {
    let active = true
    Promise.all([listVehicles(), listMaintenance()])
      .then(([vehicleList, maintenanceList]) => {
        if (active) {
          setVehicles(vehicleList.results)
          setRecords(maintenanceList.results)
        }
      })
      .catch((requestError: unknown) => { if (active) setError(loadError(requestError, 'Não foi possível carregar as manutenções.')) })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await startMaintenance({
        vehicle_id: Number(vehicleId),
        reason: reason.trim(),
        ...(mileage ? { mileage: Number(mileage) } : {}),
      })
      await refresh()
      setReason('')
      setMileage('')
      setVehicleId('')
      setMessage('Veículo enviado para manutenção.')
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível iniciar a manutenção.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleRelease(record: MaintenanceRecord) {
    setError('')
    setMessage('')
    try {
      await releaseMaintenance(record.id)
      await refresh()
      setMessage(`Veículo ${record.vehicle_plate} liberado.`)
    } catch (requestError) {
      setError(loadError(requestError, 'Não foi possível liberar o veículo.'))
    }
  }

  const columns: TableColumn<MaintenanceRecord>[] = [
    { key: 'vehicle_plate', header: 'Placa' },
    { key: 'vehicle_model', header: 'Veículo' },
    { key: 'reason', header: 'Motivo' },
    { key: 'mileage', header: 'Quilometragem', renderCell: (record) => `${record.mileage.toLocaleString('pt-BR')} km` },
    { key: 'started_at', header: 'Início', renderCell: (record) => new Date(record.started_at).toLocaleString('pt-BR') },
    { key: 'completed_at', header: 'Situação', renderCell: (record) => record.completed_at ? `Liberado em ${new Date(record.completed_at).toLocaleDateString('pt-BR')}` : <Badge label="Ativa" variant="warning" /> },
    {
      key: 'id',
      header: 'Ações',
      renderCell: (record) => record.completed_at ? null : <Button label="Liberar veículo" onClick={() => handleRelease(record)} size="sm" variant="secondary" />,
    },
  ]

  return (
    <FleetLayout description="Acompanhe revisões e avarias, e devolva veículos liberados à frota." title="Manutenção">
      <VStack as="section" aria-label="Iniciar manutenção" gap={3}>
        <Heading level={2}>Enviar veículo para manutenção</Heading>
        <form onSubmit={handleSubmit}>
          <VStack gap={3}>
            <Grid columns={{ minWidth: 220, max: 3 }} gap={3}>
              <Field inputID="maintenance-vehicle" label="Veículo">
                <select className="native-control" id="maintenance-vehicle" required value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
                  <option value="">Selecione um veículo</option>
                  {vehicles.filter((vehicle) => vehicle.status !== 'MAINTENANCE').map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.plate} · {vehicle.model} · {statusLabels[vehicle.status]}</option>)}
                </select>
              </Field>
              <Field inputID="maintenance-reason" label="Motivo">
                <input className="native-control" id="maintenance-reason" maxLength={255} required value={reason} onChange={(event) => setReason(event.target.value)} />
              </Field>
              <Field inputID="maintenance-mileage" label="Quilometragem (opcional)" isOptional>
                <input className="native-control" id="maintenance-mileage" min="0" type="number" value={mileage} onChange={(event) => setMileage(event.target.value)} />
              </Field>
            </Grid>
            <HStack className="form-actions">
              <Button isDisabled={isSubmitting || vehicles.length === 0} label={isSubmitting ? 'Registrando...' : 'Iniciar manutenção'} type="submit" />
            </HStack>
          </VStack>
        </form>
      </VStack>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
      {isLoading ? <Text as="p" role="status">Carregando manutenções...</Text> : (
        <VStack as="section" aria-label="Histórico de manutenção" gap={2}>
          <Heading level={2}>Histórico ({records.length})</Heading>
          <section className="fleet-table-wrap" aria-label="Tabela de manutenções">
            <Table columns={columns} data={records} emptyState={<Text as="p">Nenhum registro de manutenção.</Text>} hasHover idKey="id" />
          </section>
        </VStack>
      )}
    </FleetLayout>
  )
}