# Giro frontend

Interface React do Giro, construída com Vite e o design system Astryx. O tema
Neutral é aplicado globalmente; as instruções geradas para agentes estão em
[AGENTS.md](./AGENTS.md).

## Desenvolvimento

```bash
npm ci
npm run dev
```

Validação:

```bash
npm run build
npm run lint
npm run test -- --run
```

Os componentes Astryx são importados por entrada, como
`@astryxdesign/core/Button`. Para consultar componentes, templates e tokens,
use `npx astryx component`, `npx astryx template` e `npx astryx docs tokens`.
