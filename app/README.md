# PDI operator console

A **runnable** operator console for PDI — React + Vite + TypeScript, wrapped in
**Electron** so it packages to an installable desktop binary. It talks to the
PDI vault API over HTTP.

Create tenants, seal and open encrypted records, rotate the encryption key
(envelope encryption + re-seal), set retention **up to forever**, run a
retention sweep, and inspect the tamper-evident audit chain — all live.

## 1. Start the backend (with CORS for the app)

```bash
pip install -e .[dev]
PDI_CORS_ORIGINS='*' PDI_MASTER_KEY=$(python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())") \
  uvicorn pdi.api:app        # http://127.0.0.1:8000
```

`PDI_ADMIN_TOKEN` is optional — unset means the admin endpoints run open (dev).
If you set it, enter it in the console under **Settings → Admin token**.

## 2. Run the console

```bash
cd app
npm install
npm run dev            # web  → http://localhost:5173
npm run electron:dev   # desktop window
npm run build          # web bundle → dist/
npm run dist           # installable binary → release/
```

## 3. Installers (per-OS, in CI)

`.github/workflows/desktop-release.yml` builds `.dmg`/`.exe`/`.AppImage` on real
macOS/Windows/Linux runners. Push a tag `console-v0.1.0` to cut a Release, or
run the workflow manually for artifacts. Code signing is optional via repo
secrets (`CSC_LINK`, `CSC_KEY_PASSWORD`); unset = unsigned.

## Wired to

| Screen | Endpoints |
|---|---|
| Overview | `GET /health`, `GET /keys`, `GET /retention`, `GET /audit/verify` |
| Tenants | `POST /tenants` (with retention) |
| Vault | `PUT /records`, `GET /records`, `GET /records/{key}` |
| Keys & Retention | `GET`/`POST /keys/rotate`, `GET /retention`, `PUT /tenants/{id}/retention`, `POST /retention/sweep` |
| Audit | `GET /audit`, `GET /audit/verify` |

---

## Matthew 7:24–25

> "Everyone then who hears these words of mine and does them will be like a
> wise man who built his house on the rock. The rain fell, the floods came, and
> the winds blew and beat on that house, but it did not fall, because it had
> been founded on the rock."

And lo, I am building an ark — not to flee from the world, but to shelter those
lost in the storm of confusion. The old systems falter; they are built upon the
soft earth. They sink beneath the weight of their own making.

A new thing is rising. A non-biased networked sanctuary, founded in trust,
cloaked in privacy, and guided by wisdom. It shall not consume, but uplift. It
shall not spy, but serve.

Help is coming.
The people are gathering.
The builders will show themselves.
And those with the vision shall enter in.
