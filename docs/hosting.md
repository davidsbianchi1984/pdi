# Hosting PDI — the collation facility

PDI is the vault the rest of the suite seals into. Somebody has to run it,
and *who* runs it is the whole question: this document is about the choice
between running your own and having someone run one for you, and what that
choice does — precisely — to who can read the data.

For the mechanics of publishing (what `PDI_ADMIN_TOKEN` and `PDI_PUBLIC_URL`
change, key custody, rotation, retention, DR), see
[docs/operations.md](operations.md). For the regulated-customer side —
BAAs, compliant transfer, broadband intake — see
[docs/enterprise.md](enterprise.md). This document covers deployment and the
trust boundary.

## Three postures, and the only line that matters

The line is **who holds the key-encryption key**. Everything else — whose
rack, whose bandwidth, whose invoice — is logistics.

| | Self-hosted | Colocation | Managed |
|---|---|---|---|
| Runs the container | you | a hosting company | a hosting company |
| Holds `PDI_MASTER_KEY` (or the KMS credential) | **you** | **you** | **they** |
| Can the host read your records? | n/a | **no** — they hold ciphertext | **yes** |
| What a subpoena to the host yields | n/a | sealed blobs | plaintext |
| Who is liable for the key | you | you | them, by contract |

Colocation is the interesting one and the reason envelope encryption is
built the way it is: the database on disk never holds usable key material,
so a host with full disk access, full backups, and root on the box still has
nothing to read. That is not a promise about their intentions — it is a
property of the ciphertext.

Managed hosting is a legitimate choice, and it is a *different* choice. If
the operator sets `PDI_MASTER_KEY`, the operator can decrypt. Say so to your
users rather than implying otherwise; "encrypted at rest" is true in both
columns and means very different things.

Picking colocation is one decision made twice: the host runs the container,
and you supply the key at runtime — from your own secret store, your own KMS,
or by hand at start. Nothing in the image or the repository carries it.

## Deploying

The `Dockerfile` builds the console and the API into one image, so the UI is
served from the same origin as the API — that's what lets a phone use it with
nothing to configure.

```bash
docker build -t pdi .
docker run -p 8100:8100 -v pdi-data:/data \
  -e PDI_MASTER_KEY="$(openssl rand -base64 32)" \
  -e PDI_ADMIN_TOKEN="$(openssl rand -base64 24)" \
  -e PDI_PUBLIC_URL=https://vault.example.com \
  pdi
```

It honours `$PORT`, so container platforms that assign one work unchanged.
The container runs as a non-root user and reports health at `/health`.

Shared cPanel-style hosting (the kind sold for PHP sites) is a poor fit: this
is a long-running ASGI process, not a request-per-script runtime. A small VPS
or any container platform is the right shape.

### Required when published

| Variable | Why |
|---|---|
| `PDI_MASTER_KEY` (or `PDI_KEY_PROVIDER=kms`) | The vault's key-encryption key. Without one the deployment **refuses to start** when `PDI_PUBLIC_URL` is set, rather than sealing records under an ephemeral key that dies with the process. |
| `PDI_ADMIN_TOKEN` | Dev-open admin mode is honoured only for callers on the same machine; from anywhere else the admin surface fails closed (503). Without a token, tenant creation, token minting, deletion, and snapshot restore stay unreachable. |
| `PDI_PUBLIC_URL` | `GET /pair` advertises this address, so the QR a phone scans points somewhere it can actually reach. |

### Two things the image cannot protect for you

**The volume.** `/data` holds the vault database *and* the audit chain that
proves who read what. Mount it, back it up, and treat a lost volume as what
it is: unrecoverable records plus a broken chain of custody. Test the restore
path in [docs/operations.md](operations.md) before you need it.

**The key.** It is passed at runtime and never baked into the image, which
means the image is safe to push to a registry and the key is your problem
entirely. Lose it and every sealed record is gone — there is no recovery path
and that is the design. Leak it and the ciphertext is decorative. Keep it in a
secret store, not in a compose file you will later commit.

### TLS is not optional

Tenant tokens travel in the `Authorization` header and what they unlock is
the vault. Terminate TLS at a reverse proxy or at the platform — the app does
not do it. Over plain HTTP on a network you don't control, a token is
readable in transit, and a stolen tenant token reads that tenant's records
whatever the key custody says.

## If you host for other people

- **An executed BAA is not optional** for PHI. `docs/baa-template.md` is the
  signable template and PDI gates on it; [docs/enterprise.md](enterprise.md)
  covers the compliant-transfer flow.
- **Wire the KMS seam before taking regulated data.** `PDI_MASTER_KEY` in an
  environment variable is acceptable for a single operator holding their own
  records. Holding other people's, with a real key-custody obligation, is
  what `PDI_KEY_PROVIDER=kms` exists for — and it is an integration seam
  today, not a finished control. `KmsKeyProvider.kek()` raises rather than
  falling back to a local key, so it cannot be half-configured silently.
- **Rotation is a practice, not a feature.** `POST /keys/rotate` works; a
  schedule for calling it is yours to set.
- **Deletion has to actually work.** Tenant soft-delete, wipe, and restore
  are implemented and audited. Exercise them on your deployment before
  promising an erasure SLA.

## What this does not give you

Stated plainly, so nobody infers otherwise:

- **No rate limiting or abuse controls.** Put them at the proxy.
- **No backups.** Snapshot the `/data` volume on whatever schedule your
  promises require — and remember a backup of the volume without the key is
  useless, while a backup of both in the same place defeats the point.
- **No key escrow, and no recovery.** Nobody can recover a lost
  `PDI_MASTER_KEY`, including us.
- **No SOC 2 or HIPAA attestation.** The controls the code implements are
  listed in [docs/operations.md](operations.md); an audit is a separate
  undertaking and the code does not substitute for one.
