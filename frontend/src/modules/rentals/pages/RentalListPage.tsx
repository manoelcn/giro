import { useEffect, useState, type FormEvent } from 'react'
import { Badge } from '@astryxdesign/core/Badge'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Section } from '@astryxdesign/core/Section'
import { Text } from '@astryxdesign/core/Text'
import { VStack } from '@astryxdesign/core/VStack'

import { listRentals, type OverdueAlert, type RentalList } from '../api/rentals'
import { Feedback, Page } from '../../../shared/ui/Page'

interface RentalFilters {
  customer_id: string
  status: string
  pickup_branch_id: string
  starts_at: string
  expected_return_at: string
}

const emptyFilters: RentalFilters = {
  customer_id: '',
  status: '',
  pickup_branch_id: '',
  starts_at: '',
  expected_return_at: '',
}

function alertForRental(alerts: OverdueAlert[], rentalId: number) {
  return alerts.filter((alert) => alert.rental_id === rentalId)
}

export function RentalListPage() {
  const [filters, setFilters] = useState(emptyFilters)
  const [rentals, setRentals] = useState<RentalList | null>(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  async function loadRentals(query: Record<string, string> = {}) {
    setError('')
    setIsLoading(true)
    try {
      setRentals(await listRentals(query))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível carregar as locações.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    let active = true
    listRentals()
      .then((result) => {
        if (active) {
          setRentals(result)
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Não foi possível carregar as locações.',
          )
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [])

  async function handleFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const activeFilters = Object.fromEntries(
      Object.entries(filters).filter(([, value]) => value.trim() !== ''),
    )
    await loadRentals(activeFilters)
  }

  return (
    <Page
      description="Filtre o histórico por cliente, situação, filial e período."
      eyebrow="Locações"
      title="Lista de locações"
    >
      <form onSubmit={handleFilter}>
        <VStack gap={4}>
          <Grid columns={{ minWidth: 240, max: 3 }} gap={4}>
          <Field inputID="rental-customer-id" label="Cliente">
          <input
            className="native-control"
            id="rental-customer-id"
            min="1"
            type="number"
            value={filters.customer_id}
            onChange={(event) =>
              setFilters((current) => ({ ...current, customer_id: event.target.value }))
            }
          />
          </Field>
          <Field inputID="rental-status" label="Situação">
          <select
            className="native-control"
            id="rental-status"
            value={filters.status}
            onChange={(event) =>
              setFilters((current) => ({ ...current, status: event.target.value }))
            }
          >
            <option value="">Todas</option>
            <option value="RESERVED">Reservada</option>
            <option value="PICKED_UP">Em andamento</option>
            <option value="OVERDUE">Atrasada</option>
            <option value="RETURNED">Devolvida</option>
            <option value="COMPLETED">Finalizada</option>
            <option value="CANCELED">Cancelada</option>
          </select>
          </Field>
          <Field inputID="rental-pickup-branch-id" label="Filial de retirada">
          <input
            className="native-control"
            id="rental-pickup-branch-id"
            min="1"
            type="number"
            value={filters.pickup_branch_id}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                pickup_branch_id: event.target.value,
              }))
            }
          />
          </Field>
          <Field inputID="rental-starts-at" label="Início do período">
          <input
            className="native-control"
            id="rental-starts-at"
            type="date"
            value={filters.starts_at}
            onChange={(event) =>
              setFilters((current) => ({ ...current, starts_at: event.target.value }))
            }
          />
          </Field>
          <Field inputID="rental-expected-return-at" label="Fim do período">
          <input
            className="native-control"
            id="rental-expected-return-at"
            type="date"
            value={filters.expected_return_at}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                expected_return_at: event.target.value,
              }))
            }
          />
          </Field>
          </Grid>
          <HStack className="form-actions">
            <Button
              isDisabled={isLoading}
              label="Aplicar filtros"
              type="submit"
            />
          </HStack>
        </VStack>
      </form>

      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {isLoading && <Text as="p" role="status">Carregando locações...</Text>}
      {!isLoading && rentals && (
        <VStack as="section" aria-label="Locações encontradas" gap={2}>
          <Heading level={2}>Resultados ({rentals.count})</Heading>
          {rentals.results.length === 0 ? (
            <Text as="p">Nenhuma locação encontrada.</Text>
          ) : (
            rentals.results.map((rental) => (
              <Section key={rental.id} padding={3} variant="transparent">
                <VStack as="article" gap={2}>
                  <HStack align="center" gap={2} wrap="wrap">
                    <Heading level={3}>
                      {rental.status === 'OVERDUE'
                        ? `Locação #${rental.id} atrasada`
                        : `Locação #${rental.id}`}
                    </Heading>
                    <Badge
                      label={rental.status}
                      variant={
                        rental.status === 'OVERDUE'
                          ? 'warning'
                          : rental.status === 'COMPLETED'
                            ? 'success'
                            : rental.status === 'CANCELED'
                              ? 'neutral'
                              : 'info'
                      }
                    />
                  </HStack>
                  <Text as="p">Cliente #{rental.customer_id}</Text>
                  <Text as="p">Filial de retirada: #{rental.pickup_branch_id}</Text>
                  <Text as="p">
                    Filial prevista de devolução: #{rental.return_branch_id}
                  </Text>
                  <Text as="p">
                    Filial real de devolução:{' '}
                    {rental.actual_return_branch_id
                      ? `#${rental.actual_return_branch_id}`
                      : 'Pendente'}
                  </Text>
                  {alertForRental(rentals.overdue_alerts, rental.id).map((alert) => (
                    <VStack
                      as="aside"
                      className="feedback feedback-error"
                      gap={1}
                      key={alert.affected_reservation_id}
                    >
                      <Text as="p" weight="semibold">
                        Reserva futura #{alert.affected_reservation_id} afetada
                      </Text>
                      <Text as="p">
                        A reserva não será realocada automaticamente.
                      </Text>
                      {alert.equivalent_vehicle_ids.map((vehicleId) => (
                        <Text as="p" key={vehicleId}>
                          Veículo equivalente disponível: #{vehicleId}
                        </Text>
                      ))}
                    </VStack>
                  ))}
                </VStack>
              </Section>
            ))
          )}
        </VStack>
      )}
    </Page>
  )
}
