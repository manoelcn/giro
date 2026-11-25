import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RentalListPage } from '../pages/RentalListPage'
import { listRentals } from '../api/rentals'

vi.mock('../api/rentals', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/rentals')>()
  return {
    ...actual,
    listRentals: vi.fn(),
  }
})

const rentalList = {
  count: 1,
  next: null,
  results: [
    {
      id: 77,
      customer_id: 41,
      status: 'OVERDUE',
      pickup_branch_id: 3,
      return_branch_id: 5,
      actual_return_branch_id: null,
      starts_at: '2030-01-01T10:00:00Z',
      expected_return_at: '2030-01-04T10:00:00Z',
    },
  ],
  overdue_alerts: [
    {
      rental_id: 77,
      affected_reservation_id: 102,
      equivalent_vehicle_ids: [88],
    },
  ],
}

describe('rental list page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listRentals).mockResolvedValue(rentalList)
  })

  it('shows overdue alerts and available equivalent vehicles without reassignment', async () => {
    render(<RentalListPage />)

    expect(await screen.findByText('Locação #77 atrasada')).toBeInTheDocument()
    expect(screen.getByText('Reserva futura #102 afetada')).toBeInTheDocument()
    expect(screen.getByText('Veículo equivalente disponível: #88')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /realocar/i })).not.toBeInTheDocument()
  })

  it('filters rentals by customer, status, branch, and period', async () => {
    const user = userEvent.setup()
    render(<RentalListPage />)
    await screen.findByText('Locação #77 atrasada')

    await user.type(screen.getByLabelText('Cliente'), '41')
    await user.selectOptions(screen.getByLabelText('Situação'), 'OVERDUE')
    await user.type(screen.getByLabelText('Filial de retirada'), '3')
    await user.type(screen.getByLabelText('Início do período'), '2030-01-01')
    await user.type(screen.getByLabelText('Fim do período'), '2030-01-05')
    await user.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    expect(listRentals).toHaveBeenLastCalledWith({
      customer_id: '41',
      status: 'OVERDUE',
      pickup_branch_id: '3',
      starts_at: '2030-01-01',
      expected_return_at: '2030-01-05',
    })
  })
})
