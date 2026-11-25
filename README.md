# Giro

Aplicação de locação de veículos em monólito modular: backend Django/DRF e frontend React/Vite.

## Requisitos

- Python 3.14
- Node.js 24.x e npm

## Executar localmente

Backend, a partir da raiz do repositório:

```bash
cd backend
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_base
.venv/bin/python manage.py runserver
```

Frontend, em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

O Vite informa a URL local ao iniciar; o Django serve a API em `http://127.0.0.1:8000/`.
O endpoint de verificação de atrasos pode ser executado com o horário atual ou com um instante ISO 8601:

```bash
cd backend
.venv/bin/python manage.py verify_overdue
.venv/bin/python manage.py verify_overdue --now 2030-01-04T11:00:01Z
```

## Módulos e contratos

- `backend/core`: exceções compartilhadas, resposta de erro do DRF e helper monetário `Decimal`.
- `backend/rentals`: reservas, locações, regras de estado, serviços, consultas e API.
- `backend/fleet`, `backend/customers`, `backend/accounts` e `backend/finance`: models mínimos, Admin e contratos iniciais dos integrantes I2–I4.
- `frontend/src/shared`: infraestrutura comum da interface e cliente HTTP.
- `frontend/src/modules`: interfaces por módulo de negócio.

Os dados de demonstração são criados ou atualizados pelo comando idempotente `python manage.py seed_base`. Os catálogos somente leitura estão disponíveis em `GET /api/fleet/vehicles`, `/api/fleet/branches`, `/api/customers/customers` e `/api/customers/insurances`; eles ficam abertos em desenvolvimento para preencher selects. Os endpoints de locação continuam exigindo autenticação.

Cada módulo é responsável por seu domínio e persistência. A integração de `rentals` com os outros módulos usa contratos de serviço e identificadores, sem ForeignKeys entre apps. Regras de negócio ficam no domínio/serviços, não em views, serializers ou componentes. Os contratos iniciais usam regras provisórias para facilitar desenvolvimento; autenticação JWT e regras finais por perfil/filial ainda dependem da integração do Integrante 4, e os fluxos de locação ainda usam fakes nos pontos não integrados.

## Persistência e concorrência

O projeto usa SQLite com transações `IMMEDIATE` e timeout de 20 segundos para serializar a confirmação de reservas antes da consulta de conflitos. SQLite continua permitindo apenas um escritor por vez; contenção acima do timeout é retornada como erro retryable `503 DATABASE_CONTENTION`, não como confirmação. Esse perfil é adequado à escala acadêmica deste projeto; produção ou maior concorrência requer reavaliar o banco, por exemplo migrando para PostgreSQL.

Todos os cálculos monetários são feitos em Python com `Decimal`, arredondados a centavos com `ROUND_HALF_UP`; não usar aritmética monetária em SQL/SQLite.

## Regras implementadas e dependências pendentes

O módulo `rentals` cobre criação e cancelamento de reservas, retirada, devolução, finalização, atraso após uma hora de tolerância, alertas de reserva futura e consultas de locações. A devolução usa transação atômica; a caução só é liberada após a quitação.

As integrações reais de disponibilidade/vistoria (I2), cliente/cotação/seguro (I3) e cobranças/caução/autenticação (I4) continuam sendo entregas de seus respectivos responsáveis. As operações financeiras e de frota externas também precisam respeitar o contrato transacional descrito em [rentals-api.md](specs/001-reservation-rental-lifecycle/contracts/rentals-api.md).

## Validação

```bash
cd backend
.venv/bin/python manage.py test core.tests rentals.tests
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

```bash
cd frontend
npm run test -- --run
npm run lint
npm run build
```

O roteiro de integração e os cenários cobertos pelos testes estão em [quickstart.md](specs/001-reservation-rental-lifecycle/quickstart.md).
