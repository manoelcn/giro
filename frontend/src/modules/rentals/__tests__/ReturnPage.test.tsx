import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ReturnPage } from '../pages/ReturnPage'
import { finalizeRental, returnRental } from '../api/rentals'

vi.mock('../api/rentals', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/rentals')>()
  return {
    ...actual,
    finalizeRental: vi.fn(),
    returnRental: vi.fn(),
  }
})

describe('return page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays the return fee breakdown and pending balance', async () => {
    const user = userEvent.setup()
    vi.mocked(returnRental).mockResolvedValue({
      id: 77,
      status: 'RETURNED',
      returned_at: '2030-01-04T10:00:00Z',
      late_day_count: 0,
      late_charge_amount: '0.00',
      inter_branch_charge_amount: '79.99',
      damage_charge_amount: '0.00',
      balance_due: '514.99',
    })
    vi.mocked(finalizeRental).mockRejectedValue(
      new Error('Saldo pendente de R$ 514,99.'),
    )
    render(<ReturnPage rentalId="77" />)

    await user.type(screen.getByLabelText('Número da vistoria de entrada'), '902')
    await user.type(screen.getByLabelText('Filial de devolução'), '5')
    await user.click(screen.getByRole('button', { name: 'Registrar devolução' }))

    expect(await screen.findByText('R$ 79,99')).toBeInTheDocument()
    expect(screen.getByText('Saldo devido: R$ 514,99')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Finalizar locação' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Saldo pendente de R$ 514,99.',
    )
    expect(finalizeRental).toHaveBeenCalledWith('77')
  })

  it('shows completion after the remaining balance is settled', async () => {
    const user = userEvent.setup()
    vi.mocked(returnRental).mockResolvedValue({
      id: 77,
      status: 'RETURNED',
      returned_at: '2030-01-04T10:00:00Z',
      late_day_count: 0,
      late_charge_amount: '0.00',
      inter_branch_charge_amount: '0.00',
      damage_charge_amount: '0.00',
      balance_due: '0.00',
    })
    vi.mocked(finalizeRental).mockResolvedValue({
      id: 77,
      status: 'COMPLETED',
      finalized_at: '2030-01-04T11:00:00Z',
    })
    render(<ReturnPage rentalId="77" />)

    await user.type(screen.getByLabelText('Número da vistoria de entrada'), '902')
    await user.type(screen.getByLabelText('Filial de devolução'), '3')
    await user.click(screen.getByRole('button', { name: 'Registrar devolução' }))
    await user.click(await screen.findByRole('button', { name: 'Finalizar locação' }))

    expect(await screen.findByText('Locação finalizada.')).toBeInTheDocument()
  })
})
