import { Navigate, Route, Routes } from "react-router-dom";

import { CustomerListPage } from "./pages/CustomerListPage";

export function CustomerRoutes() {
  return (
    <Routes>
      <Route element={<CustomerListPage />} path="" />
      <Route element={<Navigate replace to="/customers" />} path="*" />
    </Routes>
  );
}
