import { useState, type FormEvent } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { Heading } from '@astryxdesign/core/Heading'
import { HStack } from '@astryxdesign/core/HStack'
import { Section } from '@astryxdesign/core/Section'
import { VStack } from '@astryxdesign/core/VStack'

import {
  finalizeRental,
  returnRental,
  type RentalReturnResult,
} from '../api/rentals'
import { Feedback, Page } from '../../../shared/ui/Page'

interface ReturnPageProps {
  rentalId: string
}

function formatCurrency(value: string): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value))
}

export function ReturnPage({ rentalId }: ReturnPageProps) {
  const [inspectionId, setInspectionId] = useState('')
  const [returnBranchId, setReturnBranchId] = useState('')
  const [result, setResult] = useState<RentalReturnResult | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleReturn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      const returnResult = await returnRental(
        rentalId,
        Number(inspectionId),
        Number(returnBranchId),
      )
      setResult(returnResult)
      setMessage('Devolução registrada.')
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível registrar a devolução.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleFinalize() {
    setError('')
    setIsSubmitting(true)
    try {
      await finalizeRental(rentalId)
      setMessage('Locação finalizada.')
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível finalizar a locação.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Page
      description="Registre a vistoria de entrada. O saldo considera atraso, avarias e devolução em outra filial."
      eyebrow={`Locação #${rentalId}`}
      title="Devolução e finalização"
    >
      <a
        className="fleet-action-link"
        href={`/fleet/inspections?rentalId=${encodeURIComponent(rentalId)}&type=ENTRY`}
      >
        Registrar vistoria de entrada
      </a>
      <form onSubmit={handleReturn}>
        <VStack gap={4}>
          <Grid columns={{ minWidth: 240, max: 2 }} gap={4}>
            <Field
              inputID="return-inspection-id"
              label="Número da vistoria de entrada"
            >
              <input
                className="native-control"
                id="return-inspection-id"
                required
                min="1"
                type="number"
                value={inspectionId}
                onChange={(event) => setInspectionId(event.target.value)}
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
                value={returnBranchId}
                onChange={(event) => setReturnBranchId(event.target.value)}
              />
            </Field>
          </Grid>
          <HStack className="form-actions">
            <Button
              isDisabled={isSubmitting}
              label="Registrar devolução"
              type="submit"
            />
          </HStack>
        </VStack>
      </form>

      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
      {result && (
        <Section aria-label="Resumo da devolução" padding={4} variant="muted">
          <VStack gap={3}>
            <Heading level={2}>Valores da devolução</Heading>
            <VStack as="dl" gap={2}>
              <HStack as="div" justify="between">
                <dt>Dias de atraso</dt>
                <dd>{result.late_day_count}</dd>
              </HStack>
              <HStack as="div" justify="between">
                <dt>Encargos de atraso</dt>
                <dd>{formatCurrency(result.late_charge_amount)}</dd>
              </HStack>
              <HStack as="div" justify="between">
                <dt>Taxa entre filiais</dt>
                <dd>{formatCurrency(result.inter_branch_charge_amount)}</dd>
              </HStack>
              <HStack as="div" justify="between">
                <dt>Danos</dt>
                <dd>{formatCurrency(result.damage_charge_amount)}</dd>
              </HStack>
              <HStack as="div" className="quote-total" justify="between">
                <dt>
                  Saldo devido: {formatCurrency(result.balance_due)}
                </dt>
                <dd>{result.status}</dd>
              </HStack>
            </VStack>
            <HStack className="form-actions">
              <Button
                isDisabled={isSubmitting}
                label="Finalizar locação"
                onClick={handleFinalize}
              />
            </HStack>
          </VStack>
        </Section>
      )}
    </Page>
  )
}
