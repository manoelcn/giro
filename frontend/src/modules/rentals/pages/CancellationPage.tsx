import { useEffect, useState } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Section } from '@astryxdesign/core/Section'
import { Text } from '@astryxdesign/core/Text'
import { VStack } from '@astryxdesign/core/VStack'

import {
  cancelReservation,
  getCancellationQuote,
  type CancellationQuote,
  type CancellationResult,
} from '../api/reservations'
import { Feedback, Page } from '../../../shared/ui/Page'

interface CancellationPageProps {
  reservationId: string
}

function formatCurrency(value: string): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value))
}

export function CancellationPage({ reservationId }: CancellationPageProps) {
  const [quote, setQuote] = useState<CancellationQuote | null>(null)
  const [result, setResult] = useState<CancellationResult | null>(null)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let active = true
    getCancellationQuote(reservationId)
      .then((cancellationQuote) => {
        if (active) {
          setQuote(cancellationQuote)
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Não foi possível consultar as condições do cancelamento.',
          )
        }
      })
    return () => {
      active = false
    }
  }, [reservationId])

  async function handleCancel() {
    setError('')
    setIsSubmitting(true)
    try {
      setResult(await cancelReservation(reservationId))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível cancelar a reserva.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Page
      description="Confira a condição do cancelamento antes de confirmar."
      eyebrow={`Reserva #${reservationId}`}
      title="Cancelar reserva"
    >
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {!quote && !error && (
        <Text as="p" role="status">Consultando condições...</Text>
      )}
      {quote && !result && (
        <Section aria-label="Condição do cancelamento" padding={4} variant="muted">
          <VStack gap={3}>
            <Heading level={2}>Condição do cancelamento</Heading>
            {quote.cancellation_charge ? (
              <Text as="p">
                Cobrança pendente de{' '}
                <Text as="span" weight="semibold">
                  {formatCurrency(quote.cancellation_charge.amount)}
                </Text>
                . O pagamento não é necessário para cancelar.
              </Text>
            ) : (
              <Text as="p">Cancelamento gratuito.</Text>
            )}
            <HStack className="form-actions">
              <Button
                isDisabled={isSubmitting}
                label="Confirmar cancelamento"
                onClick={handleCancel}
              />
            </HStack>
          </VStack>
        </Section>
      )}
      {result && (
        <Feedback role="status" tone="success">
          {result.cancellation_charge
            ? `Reserva cancelada. Cobrança pendente: ${formatCurrency(result.cancellation_charge.amount)}`
            : 'Reserva cancelada sem cobrança.'}
        </Feedback>
      )}
    </Page>
  )
}
