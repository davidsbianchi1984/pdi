# Contributing to PDI

Thanks for your interest! PDI (Private Data Infrastructure) is one of three
interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)); see
[docs/tandem.md](docs/tandem.md) for how they fit together.

## Development setup

```bash
pip install -e .[dev]
export PDI_MASTER_KEY=$(python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())")
pytest                     # tests generate their own ephemeral keys
uvicorn pdi.api:app
```

The tests set their own isolated database and master key per run, so no
persistent state or real KMS is needed for local development.

## Guidelines

- **Tests pass, and cover new behavior.** Run `pytest` before opening a PR; add
  tests for any new endpoint or crypto/retention/audit path. The console must
  still build (`cd app && npm run build`) — CI checks both.
- **Never weaken the guarantees.** Plaintext must never touch disk or the audit
  chain; keep AAD binding on every seal; the audit log stays append-only and
  hash-chained (never prune or edit it).
- **Keep tenants isolated.** Every data path is tenant-scoped; one tenant must
  never read or write another's records.
- **Match the surrounding style.** Standard-library-first Python (plus
  `cryptography`); keep comments at the density of the file you're editing.

## Pull requests

1. Branch off `main`.
2. Make the change with tests; keep commits focused.
3. Open a PR describing the what and why. CI runs `pytest` and the console
   smoke build.

By contributing you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
