import { useState, type FormEvent } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Section } from '@astryxdesign/core/Section'
import { VStack } from '@astryxdesign/core/VStack'

import {
  createReservation,
  quoteReservation,
  type ReservationInput,
  type ReservationQuote,
} from '../api/reservations'
import { Feedback, Page } from '../../../shared/ui/Page'

interface ReservationForm {
  customer_id: string
  vehicle_id: string
  starts_at: string
  expected_return_at: string
  pickup_branch_id: string
  return_branch_id: string
  insurance_id: string
}

const initialForm: ReservationForm = {
  customer_id: '',
  vehicle_id: '',
  starts_at: '',
  expected_return_at: '',
  pickup_branch_id: '',
  return_branch_id: '',
  insurance_id: '',
}

function toInput(form: ReservationForm): ReservationInput {
  return {
    customer_id: Number(form.customer_id),
    vehicle_id: Number(form.vehicle_id),
    starts_at: new Date(form.starts_at).toISOString(),
    expected_return_at: new Date(form.expected_return_at).toISOString(),
    pickup_branch_id: Number(form.pickup_branch_id),
    return_branch_id: Number(form.return_branch_id),
    insurance_id: form.insurance_id ? Number(form.insurance_id) : null,
  }
}

function formatCurrency(value: string): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value))
}

export function NewReservationPage() {
  const [form, setForm] = useState(initialForm)
  const [quote, setQuote] = useState<ReservationQuote | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(field: keyof ReservationForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
    setQuote(null)
    setMessage('')
  }

  async function handleQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      setQuote(await quoteReservation(toInput(form)))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível consultar a cotação.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleConfirm() {
    if (!quote) {
      return
    }
    setError('')
    setIsSubmitting(true)
    try {
      const reservation = await createReservation({
        ...toInput(form),
        accepted_total: quote.quoted_total,
      })
      setMessage(`Reserva #${reservation.id} confirmada.`)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível confirmar a reserva.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Page
      description="Consulte o valor e confirme as condições antes de reservar."
      eyebrow="Locações"
      title="Nova reserva"
    >
      <form onSubmit={handleQuote}>
        <VStack gap={4}>
          <Grid columns={{ minWidth: 240, max: 3 }} gap={4}>
            <Field inputID="customer-id" label="Cliente">
              <input
                className="native-control"
                id="customer-id"
                required
                min="1"
                type="number"
                value={form.customer_id}
                onChange={(event) =>
                  updateField('customer_id', event.target.value)
                }
              />
            </Field>
            <Field inputID="vehicle-id" label="Veículo">
              <input
                className="native-control"
                id="vehicle-id"
                required
                min="1"
                type="number"
                value={form.vehicle_id}
                onChange={(event) => updateField('vehicle_id', event.target.value)}
              />
            </Field>
            <Field inputID="starts-at" label="Retirada">
              <input
                className="native-control"
                id="starts-at"
                required
                type="datetime-local"
                value={form.starts_at}
                onChange={(event) => updateField('starts_at', event.target.value)}
              />
            </Field>
            <Field
              inputID="expected-return-at"
              label="Devolução prevista"
            >
              <input
                className="native-control"
                id="expected-return-at"
                required
                type="datetime-local"
                value={form.expected_return_at}
                onChange={(event) =>
                  updateField('expected_return_at', event.target.value)
                }
              />
            </Field>
            <Field
              inputID="pickup-branch-id"
              label="Filial de retirada"
            >
              <input
                className="native-control"
                id="pickup-branch-id"
                required
                min="1"
                type="number"
                value={form.pickup_branch_id}
                onChange={(event) =>
                  updateField('pickup_branch_id', event.target.value)
                }
              />
            </Field>
            <Field
              inputID="return-branch-id"
              label="Filial de devolução"
            >
              <input
                className="native-control"
                id="return-branch-id"
                required
                min="1"
                type="number"
                value={form.return_branch_id}
                onChange={(event) =>
                  updateField('return_branch_id', event.target.value)
                }
              />
            </Field>
            <Field inputID="insurance-id" label="Seguro (opcional)">
              <input
                className="native-control"
                id="insurance-id"
                min="1"
                type="number"
                value={form.insurance_id}
                onChange={(event) => updateField('insurance_id', event.target.value)}
              />
            </Field>
          </Grid>
          <HStack className="form-actions">
            <Button
              isDisabled={isSubmitting}
              label="Consultar cotação"
              type="submit"
            />
          </HStack>
        </VStack>
      </form>

      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}

      {quote && (
        <Section aria-label="Resumo da cotação" padding={4} variant="muted">
          <VStack gap={3}>
            <Heading level={2}>Condições da reserva</Heading>
            <VStack as="dl" gap={2}>
              <HStack as="div" justify="between">
                <dt>Diária</dt>
                <dd>{formatCurrency(quote.daily_rate)}</dd>
              </HStack>
              <HStack as="div" justify="between">
                <dt>Primeiro dia</dt>
                <dd>{formatCurrency(quote.first_day_amount)}</dd>
              </HStack>
              <HStack as="div" className="quote-total" justify="between">
                <dt>Total</dt>
                <dd>{formatCurrency(quote.quoted_total)}</dd>
              </HStack>
            </VStack>
            <HStack className="form-actions">
              <Button
                isDisabled={isSubmitting}
                label="Confirmar reserva"
                onClick={handleConfirm}
              />
            </HStack>
          </VStack>
        </Section>
      )}
    </Page>
  )
}
