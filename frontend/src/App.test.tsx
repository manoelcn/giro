import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the Giro welcome screen', () => {
    render(<App />)

    expect(screen.getByRole('main')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Giro' })).toBeTruthy()
    expect(
      screen.getByText('Sistema de gestão de locadora'),
    ).toBeTruthy()
    expect(
      screen.getByText(/A estrutura inicial do projeto está pronta/),
    ).toBeTruthy()
  })
})
