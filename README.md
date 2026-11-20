# Giro

Sistema web para gestão de uma locadora de veículos, desenvolvido como
atividade da disciplina de Linguagem de Programação II. O projeto está na etapa de
estruturação: as regras de negócio e os módulos funcionais ainda serão
implementados.

**Repositório:** <https://github.com/manoelcn/giro>

## Tecnologias

- **Back-end:** Python, Django, Django REST Framework e SQLite para desenvolvimento.
- **Front-end:** React, TypeScript e Vite.

## Estrutura

```text
giro/
├── backend/
│   ├── api/             # Endpoints e componentes da API REST
│   ├── config/          # Configurações e rotas do Django
│   ├── domain/
│   │   ├── entities/    # Entidades de negócio em Python puro
│   │   ├── enums/       # Enumerações do domínio
│   │   └── exceptions/  # Exceções de negócio
│   ├── persistence/     # Persistência com Django
│   ├── repositories/    # Conversão entre domínio e persistência
│   ├── services/        # Casos de uso e regras de negócio
│   ├── manage.py
│   └── requirements.txt
├── docs/                # Documentação e diagrama UML
├── frontend/            # Aplicação React + TypeScript + Vite
└── README.md
```

O domínio e as regras de negócio devem permanecer independentes das views,
serializers e componentes React.

## Pré-requisitos

- Python 3.12 ou superior
- Node.js 22.12 ou superior e npm

## Como executar

O back-end e o front-end são iniciados separadamente. Abra um terminal para cada
um.

### Back-end

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

No Windows PowerShell, ative o ambiente com
`.venv\Scripts\Activate.ps1`.

No Windows PowerShell, copie o exemplo de configuração com
`Copy-Item .env.example .env`.

Edite o arquivo `backend/.env` e substitua `DJANGO_SECRET_KEY` por uma chave
gerada com:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

As variáveis disponíveis estão documentadas em
[backend/.env.example](./backend/.env.example):

- `DJANGO_SECRET_KEY`: chave criptográfica usada pelo Django.
- `DJANGO_DEBUG`: `true` para desenvolvimento e `false` para produção.
- `DJANGO_ALLOWED_HOSTS`: hosts separados por vírgula.

Nunca envie `backend/.env` para o Git. O arquivo está protegido pelo
`.gitignore` e contém somente valores locais.

- API de verificação: <http://127.0.0.1:8000/api/health/>
- Administração Django: <http://127.0.0.1:8000/admin/>

O endpoint de verificação deve responder `{"status":"ok"}`.

### Front-end

```bash
cd frontend
npm install
npm run dev
```

O Vite informa no terminal o endereço local da aplicação. Para validar o
build, lint e testes unitários:

```bash
npm run build
npm run lint
npm test
```

### Verificação do back-end

Com o ambiente virtual ativado e a partir da pasta `backend/`:

```bash
python manage.py check
python manage.py test
```

Os testes ficam em diretórios `tests/` dentro de cada módulo do backend. O
diretório deve conter `__init__.py`, e os arquivos devem começar com `test_` ou
terminar com `_test.py`. O Django usa [config/settings.py](./backend/config/settings.py)
como configuração padrão e cria automaticamente um banco de dados temporário
durante os testes.

## Desenvolvimento

- Identificadores de código, pastas e rotas da API são escritos em inglês.
- Textos da interface e documentação são escritos em português.
- SQLite é o banco local inicial; os arquivos do banco e o ambiente virtual não
  devem ser versionados.
- A chave padrão do Django é somente para desenvolvimento. Configure
  `DJANGO_SECRET_KEY` e `DJANGO_DEBUG` adequadamente antes de qualquer uso fora
  do ambiente local.
- A integração do front-end com a API, autenticação e regras de negócio ainda
  serão desenvolvidas.

## Grupo

[Joao Vitor Guimaraes Albarello](https://github.com/jvguimaraess), [Kaua Vinicius Ramos Campos](https://github.com/kauacampostp), [Manoel Candido Neto](https://github.com/manoelcn) e [Maria Fernanda Magalhaes Freitas](https://github.com/nandamfmf).
