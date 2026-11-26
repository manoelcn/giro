import type { ComponentPropsWithoutRef } from "react";
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { AppShell } from "@astryxdesign/core/AppShell";
import { TopNav, TopNavHeading, TopNavItem } from "@astryxdesign/core/TopNav";

import { CustomerRoutes } from "./modules/customers/routes";
import { FleetRoutes } from "./modules/fleet/routes";
import { RentalRoutes } from "./modules/rentals/routes";

type InternalLinkProps = ComponentPropsWithoutRef<"a"> & { href?: string };

function InternalLink({ href = "/reservations", ...props }: InternalLinkProps) {
  return <Link to={href} {...props} />;
}

function App() {
  return (
    <BrowserRouter>
      <ApplicationShell />
    </BrowserRouter>
  );
}

function ApplicationShell() {
  const { pathname } = useLocation();

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
            isSelected={pathname === "/reservations"}
            label="Reservas"
          />
          <TopNavItem
            as={InternalLink}
            href="/reservations/new"
            isSelected={pathname === "/reservations/new"}
            label="Nova reserva"
          />
          <TopNavItem
            as={InternalLink}
            href="/rentals"
            isSelected={pathname.startsWith("/rentals")}
            label="Locações"
          />
          <TopNavItem
            as={InternalLink}
            href="/customers"
            isSelected={pathname.startsWith("/customers")}
            label="Clientes"
          />
          <TopNavItem
            as={InternalLink}
            href="/fleet/vehicles"
            isSelected={pathname.startsWith("/fleet")}
            label="Frota"
          />
        </TopNav>
      }
      variant="surface"
    >
      <Routes>
        <Route element={<CustomerRoutes />} path="/customers/*" />
        <Route element={<FleetRoutes />} path="/fleet/*" />
        <Route element={<RentalRoutes />} path="*" />
      </Routes>
    </AppShell>
  );
}

export default App;
