import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CustomerListPage } from "../pages/CustomerListPage";
import { listCustomers } from "../api/customers";

vi.mock("../api/customers", () => ({
  listCustomers: vi.fn(),
}));

describe("customer list page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the customers returned by the API", async () => {
    vi.mocked(listCustomers).mockResolvedValue({
      count: 1,
      next: null,
      results: [
        {
          id: 1,
          full_name: "Ana Silva",
          national_id: "11111111111",
          email: "ana@example.test",
          phone: "11990000000",
          birth_date: "1990-05-10",
          status: "ACTIVE",
        },
      ],
    });

    render(<CustomerListPage />);

    expect(await screen.findByText("Ana Silva")).toBeInTheDocument();
    expect(screen.getByText("ana@example.test")).toBeInTheDocument();
    expect(screen.getByText("10/05/1990")).toBeInTheDocument();
    expect(screen.getByText("Ativo")).toBeInTheDocument();
  });

  it("shows the API error message", async () => {
    vi.mocked(listCustomers).mockRejectedValue(new Error("Falha de rede"));

    render(<CustomerListPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Falha de rede");
  });
});
