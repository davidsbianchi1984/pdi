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

## Four postures, and the only line that matters

The line is **who holds the key-encryption key**. Everything else — whose
rack, whose bandwidth, whose invoice — is logistics.

| | Self-hosted | Colocation | Managed | Managed + BYOK |
|---|---|---|---|---|
| Runs the container | you | a hosting company | a hosting company | a hosting company |
| Holds the key | **you** | **you** | **they** | **you** |
| Can the host read your records? | n/a | **no** | **yes** | **not at rest** |
| What a subpoena to the host yields | n/a | sealed blobs | plaintext | sealed blobs |
| Works for one tenant among many | — | no | yes | **yes** |

Colocation is the reason envelope encryption is built the way it is: the
database on disk never holds usable key material, so a host with full disk
access, full backups, and root on the box still has nothing to read. That is
not a promise about their intentions — it is a property of the ciphertext.
But it is deployment-wide: it protects *everyone* on that box or no one.

**BYOK is the per-tenant version**, and it is what makes an outsourced
collation facility workable for a customer who is one tenant among many. See
[Bring your own key](#bring-your-own-key) below.

Managed hosting without BYOK is a legitimate choice, and it is a *different*
choice. If the operator sets `PDI_MASTER_KEY`, the operator can decrypt. Say
so to your users rather than implying otherwise; "encrypted at rest" is true
in every column above and means very different things in each.

## Bring your own key

A tenant can take its own records out of the operator's reach without moving
off the operator's deployment:

```bash
# One decision, made once. Every existing record is re-sealed under your key
# in the same transaction — there is no half-migrated state.
curl -X PUT https://vault.example.com/key \
  -H "authorization: Bearer $TENANT_TOKEN" \
  -d '{"provider":"held","key":"'"$(openssl rand -base64 32)"'"}'

# Afterwards the key travels with each request and is never stored.
curl https://vault.example.com/records/my/key \
  -H "authorization: Bearer $TENANT_TOKEN" \
  -H "x-tenant-key: $MY_KEY"
```

`GET /key` reports which custody model a tenant is under and what it
guarantees. Two providers, and the difference between them is the whole
point:

| | `held` | `kms` |
|---|---|---|
| Where the key lives | you present it per request | your own KMS |
| Operator can decrypt at rest | **no** | yes, while your grant is live |
| You revoke by | withholding the key | revoking at your KMS |
| Background reseal / rotation | needs you | works |
| Status | implemented | integration seam — `KmsKeyProvider.kek()` raises |

### What `held` actually guarantees — and what it does not

**It does**: make the operator's database, backups, snapshots, and disk
images unreadable for your records without your participation. An operator
who is compelled to hand over the disk hands over ciphertext.

**It does not**: protect you from a hostile *running* operator. They run the
process, so a modified deployment could capture your key at the moment you
present it. This is a guarantee about data at rest, not about a live
adversary with root — and anyone who tells you otherwise is selling
something.

Three consequences worth accepting deliberately:

- **No escrow, no recovery.** Lose the key and those records are gone. That
  is the same property that makes the guarantee real.
- **Background jobs stop at your door.** A retention sweep still deletes your
  expired records (deletion needs no key), but the operator's reseal and
  rotation skip you and *say* they skipped you — `reseal` reports
  `customer_managed_skipped`. Rotating your own keyring is your job.
- **Handing custody back needs the key.** `DELETE /key` re-seals everything
  under the deployment's key, which means opening it first.

Adoption is all-or-nothing on purpose. A half-migrated tenant — some records
the operator can still read, some not, and no way to tell which from the
outside — is a worse position than either end state.

## The three-product beta is a different page

This page is about running PDI on its own. The live beta is four
containers on one box — PDI, its two sibling products and the shared
gateway behind one reverse proxy — and it is documented once, in QRME, at
`docs/beta-deploy.md`, beside the compose file it describes.

Once rather than three times, deliberately: it is one machine. Three copies
of a page about one box is the drift this estate keeps finding in itself, and
the copies would disagree the first time somebody fixed only the one they had
open. What belongs here is the pointer, so an operator standing in this
repository can find it.

Its § 7 is the one to read at the end of a release: all three repositories are
pulled and rebuilt every time, even for a release that changed only one of
them, because each console's version guard compares itself against whatever
backend answers its port.


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
- **Offer BYOK to anyone who asks how you protect them from yourself.** It
  is the honest answer, and it costs you nothing to enable — see
  [Bring your own key](#bring-your-own-key). `held` custody is implemented;
  the `kms` provider is still an integration seam that raises rather than
  falling back to a local key, so it cannot be half-configured silently.
- **Deployment-wide keys are still yours to manage.** `PDI_MASTER_KEY` in an
  environment variable is acceptable for a single operator holding their own
  records; for everyone who has not adopted BYOK, you are the custodian.
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
