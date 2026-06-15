# AegisQA Review Dashboard

React dashboard for reviewing generated AegisQA automation.

The dashboard can browse the backend mock ticket database and start workflows
from those seeded tickets when live ticket-data endpoints are unavailable.

## Commands

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run build
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.
