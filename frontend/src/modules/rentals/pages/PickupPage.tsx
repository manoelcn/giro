import { useState, type FormEvent } from 'react'
import { Button } from '@astryxdesign/core/Button'
import { Field } from '@astryxdesign/core/Field'
import { Grid } from '@astryxdesign/core/Grid'
import { HStack } from '@astryxdesign/core/HStack'
import { VStack } from '@astryxdesign/core/VStack'

import { pickUpRental } from '../api/rentals'
import { Feedback, Page } from '../../../shared/ui/Page'

interface PickupPageProps {
  rentalId: string
}

export function PickupPage({ rentalId }: PickupPageProps) {
  const [inspectionId, setInspectionId] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)
    try {
      await pickUpRental(rentalId, Number(inspectionId))
      setMessage('Retirada registrada.')
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível registrar a retirada.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Page
      description="A retirada exige cliente elegível, vistoria de saída registrada e caução mínima paga."
      eyebrow={`Locação #${rentalId}`}
      title="Retirada do veículo"
    >
      <form onSubmit={handleSubmit}>
        <VStack gap={4}>
          <Grid columns={{ minWidth: 240, max: 2 }} gap={4}>
            <Field
              inputID="pickup-inspection-id"
              label="Número da vistoria de saída"
            >
              <input
                className="native-control"
                id="pickup-inspection-id"
                required
                min="1"
                type="number"
                value={inspectionId}
                onChange={(event) => setInspectionId(event.target.value)}
              />
            </Field>
          </Grid>
          <HStack className="form-actions">
            <Button
              isDisabled={isSubmitting}
              label="Confirmar retirada"
              type="submit"
            />
          </HStack>
        </VStack>
      </form>
      {error && <Feedback role="alert" tone="error">{error}</Feedback>}
      {message && <Feedback role="status" tone="success">{message}</Feedback>}
    </Page>
  )
}
