import { useEffect, useState } from "react";
import { Badge } from "@astryxdesign/core/Badge";
import { Table, type TableColumn } from "@astryxdesign/core/Table";
import { Text } from "@astryxdesign/core/Text";

import { listCustomers, type Customer } from "../api/customers";
import { Feedback, Page } from "../../../shared/ui/Page";

function formatDate(isoDate: string) {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

const columns: TableColumn<Customer>[] = [
  { key: "full_name", header: "Nome" },
  { key: "email", header: "E-mail" },
  { key: "phone", header: "Telefone" },
  {
    key: "birth_date",
    header: "Nascimento",
    renderCell: (customer) => formatDate(customer.birth_date),
  },
  {
    key: "status",
    header: "Situação",
    renderCell: (customer) => (
      <Badge
        label={customer.status === "ACTIVE" ? "Ativo" : "Bloqueado"}
        variant={customer.status === "ACTIVE" ? "success" : "warning"}
      />
    ),
  },
];

export function CustomerListPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listCustomers()
      .then((result) => {
        if (active) {
          setCustomers(result.results);
        }
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Não foi possível carregar os clientes."
          );
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Page
      description="Clientes cadastrados na locadora."
      eyebrow="Clientes"
      title="Lista de clientes"
    >
      {error && (
        <Feedback role="alert" tone="error">
          {error}
        </Feedback>
      )}
      {isLoading && (
        <Text as="p" role="status">
          Carregando clientes...
        </Text>
      )}
      {!isLoading && !error && (
        <Table
          columns={columns}
          data={customers}
          emptyState={<Text as="p">Nenhum cliente cadastrado.</Text>}
          hasHover
          idKey="id"
        />
      )}
    </Page>
  );
}
