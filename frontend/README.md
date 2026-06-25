# AegisQA Review Dashboard

React dashboard for operating and reviewing AegisQA workflows.

The dashboard browses the backend demo ticket store, starts controlled agent
workflows, exposes approval and artifact-edit checkpoints, and displays local
Robot execution results.

## Commands

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run build
```

Runtime variables:

```text
VITE_API_ROOT=/api/v1
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
VITE_DEV_HOST=127.0.0.1
VITE_DEV_PORT=5173
VITE_OPERATOR_ID=demo-qa-lead
```
