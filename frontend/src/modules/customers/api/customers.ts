import { apiRequest } from "../../../shared/api/client";

export type CustomerStatus = "ACTIVE" | "BLOCKED";

export type Customer = {
  id: number;
  full_name: string;
  national_id: string;
  email: string;
  phone: string;
  birth_date: string;
  status: CustomerStatus;
};

export interface CustomerList {
  count: number;
  next: string | null;
  results: Customer[];
}

export async function listCustomers(): Promise<CustomerList> {
  return apiRequest("/customers/customers");
}
