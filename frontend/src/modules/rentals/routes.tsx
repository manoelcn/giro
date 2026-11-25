import { Navigate, Route, Routes, useParams } from 'react-router-dom'

import { NewReservationPage } from './pages/NewReservationPage'
import { PickupPage } from './pages/PickupPage'
import { CancellationPage } from './pages/CancellationPage'
import { ReservationListPage } from './pages/ReservationListPage'
import { ReturnPage } from './pages/ReturnPage'
import { RentalListPage } from './pages/RentalListPage'

function PickupRoute() {
  const { rentalId } = useParams()
  return rentalId ? <PickupPage rentalId={rentalId} /> : null
}

export function RentalRoutes() {
  return (
    <Routes>
      <Route element={<ReservationListPage />} path="/reservations" />
      <Route element={<NewReservationPage />} path="/reservations/new" />
      <Route element={<RentalListPage />} path="/rentals" />
      <Route
        element={<CancellationRoute />}
        path="/reservations/:reservationId/cancel"
      />
      <Route element={<PickupRoute />} path="/rentals/:rentalId/pick-up" />
      <Route
        element={<ReturnRoute />}
        path="/rentals/:rentalId/return"
      />
      <Route element={<Navigate replace to="/reservations" />} path="*" />
    </Routes>
  )
}

function CancellationRoute() {
  const { reservationId } = useParams()
  return reservationId ? <CancellationPage reservationId={reservationId} /> : null
}

function ReturnRoute() {
  const { rentalId } = useParams()
  return rentalId ? <ReturnPage rentalId={rentalId} /> : null
}
