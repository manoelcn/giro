import { useEffect, useState, type FormEvent } from 'react'
import { Badge } from '@astryxdesign/core/Badge'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Text } from '@astryxdesign/core/Text'
import { VStack } from '@astryxdesign/core/VStack'

import {
  getReservation,
  listReservations,
  type Reservation,
  type ReservationList,
} from '../api/reservations'
import { Feedback, Page } from '../../../shared/ui/Page'

function ReservationDetails({ reservation }: { reservation: Reservation }) {
  return (
    <VStack
      as="article"
      aria-label={`Reserva #${reservation.id}`}
      className="reservation-result"
      gap={2}
    >
      <Heading level={2}>Reserva #{reservation.id}</Heading>
      <HStack gap={2} wrap="wrap">
        <Text as="p">Situação:</Text>
        <Badge
          label={reservation.status}
          variant={reservation.status === 'CANCELED' ? 'neutral' : 'info'}
        />
      </HStack>
      <Text as="p">Locação: {reservation.rental_status ?? 'Ainda não iniciada'}</Text>
      <Text as="p">Total: R$ {reservation.quoted_total}</Text>
    </VStack>
  )
}

export function ReservationListPage() {
  const [reservations, setReservations] = useState<ReservationList | null>(null)
  const [reservation, setReservation] = useState<Reservation | null>(null)
  const [reservationId, setReservationId] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    listReservations()
      .then((result) => {
        if (active) {
          setReservations(result)
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Não foi possível carregar as reservas.',
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

  async function handleLookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setReservation(null)
    try {
      setReservation(await getReservation(reservationId))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível localizar a reserva.',
      )
    }
  }

  return (
    <Page
      description="Consulte o histórico e localize uma reserva pelo número."
      eyebrow="Locações"
      title="Reservas"
    >
      <form onSubmit={handleLookup}>
        <VStack gap={4}>
          <Grid columns={{ minWidth: 240, max: 2 }} gap={4}>
            <Field inputID="reservation-id" label="Número da reserva">
              <input
                className="native-control"
                id="reservation-id"
                required
                min="1"
                type="number"
                value={reservationId}
                onChange={(event) => setReservationId(event.target.value)}
              />
            </Field>
          </Grid>
          <HStack className="form-actions">
            <Button label="Buscar reserva" type="submit" />
          </HStack>
        </VStack>
      </form>

      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {reservation && <ReservationDetails reservation={reservation} />}
      {isLoading && <Text as="p" role="status">Carregando reservas...</Text>}
      {!isLoading && reservations && (
        <VStack as="section" aria-label="Lista de reservas" gap={2}>
          <Heading level={2}>Reservas cadastradas ({reservations.count})</Heading>
          {reservations.results.length === 0 ? (
            <Text as="p">Nenhuma reserva encontrada.</Text>
          ) : (
            reservations.results.map((item) => (
              <ReservationDetails key={item.id} reservation={item} />
            ))
          )}
        </VStack>
      )}
    </Page>
  )
}
