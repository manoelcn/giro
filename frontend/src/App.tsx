import type { ComponentPropsWithoutRef } from 'react'
import { BrowserRouter, Link, useLocation } from 'react-router-dom'
import { AppShell } from '@astryxdesign/core/AppShell'
import { TopNav, TopNavHeading, TopNavItem } from '@astryxdesign/core/TopNav'

import { RentalRoutes } from './modules/rentals/routes'

type InternalLinkProps = ComponentPropsWithoutRef<'a'> & { href?: string }

function InternalLink({ href = '/reservations', ...props }: InternalLinkProps) {
  return <Link to={href} {...props} />
}

function App() {
  return (
    <BrowserRouter>
      <ApplicationShell />
    </BrowserRouter>
  )
}

function ApplicationShell() {
  const { pathname } = useLocation()

  return (
    <AppShell
      contentPadding={4}
      height="auto"
      topNav={
        <TopNav
          heading={
            <TopNavHeading
              as={InternalLink}
              heading="Giro"
              headingHref="/reservations"
            />
          }
          label="Navegação principal"
        >
          <TopNavItem
            as={InternalLink}
            href="/reservations"
            isSelected={pathname === '/reservations'}
            label="Reservas"
          />
          <TopNavItem
            as={InternalLink}
            href="/reservations/new"
            isSelected={pathname === '/reservations/new'}
            label="Nova reserva"
          />
          <TopNavItem
            as={InternalLink}
            href="/rentals"
            isSelected={pathname.startsWith('/rentals')}
            label="Locações"
          />
        </TopNav>
      }
      variant="surface"
    >
      <RentalRoutes />
    </AppShell>
  )
}

export default App
