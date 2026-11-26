import { Navigate, Route, Routes } from 'react-router-dom'

import {
  AvailabilityPage,
  BranchManagementPage,
  InspectionPage,
  MaintenancePage,
  VehicleManagementPage,
} from './FleetPages'

export function FleetRoutes() {
  return (
    <Routes>
      <Route element={<VehicleManagementPage />} path="vehicles" />
      <Route element={<BranchManagementPage />} path="branches" />
      <Route element={<AvailabilityPage />} path="availability" />
      <Route element={<InspectionPage />} path="inspections" />
      <Route element={<MaintenancePage />} path="maintenance" />
      <Route element={<Navigate replace to="/fleet/vehicles" />} path="*" />
    </Routes>
  )
}