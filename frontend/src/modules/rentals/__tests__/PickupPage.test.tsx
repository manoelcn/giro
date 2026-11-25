import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PickupPage } from '../pages/PickupPage'
import { pickUpRental } from '../api/rentals'

vi.mock('../api/rentals', () => ({
  pickUpRental: vi.fn(),
}))

describe('pickup page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('explains a pending inspection and preserves the pickup flow', async () => {
    const user = userEvent.setup()
    vi.mocked(pickUpRental).mockRejectedValue(
      new Error('A vistoria de saída ainda não foi registrada.'),
    )
    render(<PickupPage rentalId="77" />)

    await user.type(screen.getByLabelText('Número da vistoria de saída'), '901')
    await user.click(screen.getByRole('button', { name: 'Confirmar retirada' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'A vistoria de saída ainda não foi registrada.',
    )
    expect(pickUpRental).toHaveBeenCalledWith('77', 901)
  })

  it('confirms pickup only after the backend accepts the prerequisites', async () => {
    const user = userEvent.setup()
    vi.mocked(pickUpRental).mockResolvedValue({
      id: 77,
      status: 'PICKED_UP',
      picked_up_at: '2030-01-01T10:00:00Z',
    })
    render(<PickupPage rentalId="77" />)

    await user.type(screen.getByLabelText('Número da vistoria de saída'), '901')
    await user.click(screen.getByRole('button', { name: 'Confirmar retirada' }))

    expect(await screen.findByText('Retirada registrada.')).toBeInTheDocument()
  })
})
