import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { NewReservationPage } from '../pages/NewReservationPage'
import { ReservationListPage } from '../pages/ReservationListPage'
import {
  createReservation,
  getReservation,
  listReservations,
  quoteReservation,
} from '../api/reservations'

vi.mock('../api/reservations', () => ({
  createReservation: vi.fn(),
  getReservation: vi.fn(),
  listReservations: vi.fn(),
  quoteReservation: vi.fn(),
}))

const quote = {
  daily_rate: '120.00',
  first_day_amount: '145.00',
  quoted_total: '435.00',
  currency: 'BRL',
}

describe('reservation pages', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays the quote and confirms a reservation', async () => {
    const user = userEvent.setup()
    vi.mocked(quoteReservation).mockResolvedValue(quote)
    vi.mocked(createReservation).mockResolvedValue({
      id: 102,
      rental_id: 77,
      status: 'CONFIRMED',
      starts_at: '2030-01-01T10:00:00Z',
      expected_return_at: '2030-01-04T10:00:00Z',
      quoted_total: '435.00',
    })

    render(<NewReservationPage />)

    await user.type(screen.getByLabelText('Cliente'), '41')
    await user.type(screen.getByLabelText('Veículo'), '12')
    await user.type(screen.getByLabelText('Retirada'), '2030-01-01T10:00')
    await user.type(screen.getByLabelText('Devolução prevista'), '2030-01-04T10:00')
    await user.type(screen.getByLabelText('Filial de retirada'), '3')
    await user.type(screen.getByLabelText('Filial de devolução'), '5')
    await user.click(screen.getByRole('button', { name: 'Consultar cotação' }))

    expect(await screen.findByText('R$ 435,00')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirmar reserva' }))

    await waitFor(() => expect(createReservation).toHaveBeenCalledWith(
      expect.objectContaining({ accepted_total: '435.00' }),
    ))
    expect(await screen.findByText(/Reserva #102 confirmada/)).toBeInTheDocument()
  })

  it('looks up and displays a reservation from the reservation list', async () => {
    const user = userEvent.setup()
    vi.mocked(listReservations).mockResolvedValue({
      count: 1,
      next: null,
      results: [],
    })
    vi.mocked(getReservation).mockResolvedValue({
      id: 102,
      rental_id: 77,
      status: 'CONFIRMED',
      starts_at: '2030-01-01T10:00:00Z',
      expected_return_at: '2030-01-04T10:00:00Z',
      quoted_total: '435.00',
    })

    render(<ReservationListPage />)
    await user.type(await screen.findByLabelText('Número da reserva'), '102')
    await user.click(screen.getByRole('button', { name: 'Buscar reserva' }))

    expect(await screen.findByText('Reserva #102')).toBeInTheDocument()
    expect(getReservation).toHaveBeenCalledWith('102')
  })
})
