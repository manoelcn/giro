import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CancellationPage } from '../pages/CancellationPage'
import { cancelReservation, getCancellationQuote } from '../api/reservations'

vi.mock('../api/reservations', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/reservations')>()
  return {
    ...actual,
    cancelReservation: vi.fn(),
    getCancellationQuote: vi.fn(),
  }
})

describe('cancellation page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the pending charge before confirmation and the result afterward', async () => {
    const user = userEvent.setup()
    vi.mocked(getCancellationQuote).mockResolvedValue({
      cancellation_charge: {
        type: 'CANCELLATION',
        amount: '29.00',
        status: 'PENDING',
      },
    })
    vi.mocked(cancelReservation).mockResolvedValue({
      id: 102,
      status: 'CANCELED',
      cancellation_charge: {
        type: 'CANCELLATION',
        amount: '29.00',
        status: 'PENDING',
      },
    })
    render(<CancellationPage reservationId="102" />)

    expect(await screen.findByText('R$ 29,00')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirmar cancelamento' }))

    expect(cancelReservation).toHaveBeenCalledWith('102')
    expect(await screen.findByText(/Cobrança pendente: R\$[\s\u00a0]29,00/)).toBeInTheDocument()
  })
})
