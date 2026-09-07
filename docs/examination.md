# PDI — for examination

This page is written to be checked, not believed. Every section grounds the
product in three things: the **technical problem** in the machine, the
**implementation** as built — named modules, named constants, named tests —
and a **measurable effect** that follows from the implementation and not
from a description of it.

Every `.png` under `docs/screens/` and `docs/walkthrough/` is a capture of
the running console taken by `tools/shoot_screens.py` and
`tools/walkthrough.py` against a live backend; an `.svg` is a design drawing
and is captioned as one. The suite (`python -m pytest`) reads the README —
the release banner, the release table, the gallery, the stated screen count
and the closing passage fail the build when they drift from the product.

The screens referred to below are shown in
[the README](../README.md#screenshots).

## The mechanisms on file

The numbered mechanisms in
[docs/invention-disclosure.md](docs/invention-disclosure.md). Each row
names the technical problem in the machine, the particular structure this
code uses to solve it, what that structure changes about how the machine
behaves, and where the structure is reduced to practice and held by a
test. None of them is a business arrangement written down in software or
a step a person could take with a filing cabinet; each is a specific
arrangement of keys, records, credentials and audit entries inside a
running system, and each is photographed on the screens below.

<table width="100%">
<thead>
<tr>
<th width="4%" align="left">§</th>
<th width="23%" align="left">The technical problem</th>
<th width="30%" align="left">The particular solution, as built</th>
<th width="26%" align="left">What it changes in the machine</th>
<th width="17%" align="left">Reduced to practice in</th>
</tr>
</thead>
<tbody>
<tr>
<td valign="top">1</td>
<td valign="top">Three products that share a person's records must each hold them, and whichever holds them in the clear is the one a breach reads.</td>
<td valign="top">One <strong>individually keyed encrypted vault</strong> is the seal point for the family: a guardian's biometric events, tandem exchanges and clinical captures are sealed at write time under an envelope whose key-encryption key never touches a record, with per-record provenance and a hash-chained audit history read back through a custody viewer scoped to the record owner.</td>
<td valign="top">The products keep pointers and audit entries; the plaintext exists only inside the vault's decryption path. One tenant's rows are unreadable to another, and a wiped tenant is gone from every table.</td>
<td valign="top"><code>pdi/<wbr>crypto.py</code>,<br><code>pdi/<wbr>vault.py</code> — <code>test_<wbr>one_<wbr>tenant_<wbr>cannot_<wbr>read_<wbr>another.py</code>,<br><code>test_<wbr>a_<wbr>wiped_<wbr>tenant_<wbr>is_<wbr>gone_<wbr>from_<wbr>every_<wbr>table.py</code>,<br><code>test_<wbr>the_<wbr>other_<wbr>tenants_<wbr>shelf.py</code></td>
</tr>
<tr>
<td valign="top">2</td>
<td valign="top">Whether a person's data is vaulted is decided by how a server was deployed, which the person cannot see and an operator can change.</td>
<td valign="top">Custody is a <strong>property of the plan</strong>: a free platform-custody tier holds nothing private and says so at every surface, paid tiers seal every write; the gate sits at the plan boundary, so a deployment cannot change a person's custody without changing their plan.</td>
<td valign="top">The custody promise a screen shows is the custody the write path enforces, and a BAA is a plan property the same way.</td>
<td valign="top"><code>pdi/<wbr>compliance.py</code>,<br><code>pdi/<wbr>baa.py</code> — <code>test_<wbr>baa.py</code>,<br><code>test_<wbr>hosting.py</code></td>
</tr>
<tr>
<td valign="top">3</td>
<td valign="top">Moving a vault from shared hosting to a person's own device changes the API the products call, so upgrading custody breaks the products.</td>
<td valign="top">The <strong>same vault API</strong> is served across free colocation, leased space, self-hosting and the person's own device; the hosting mode is a property of the deployment the clients read, not a different surface, and admin key rotation is performed from the product apps themselves.</td>
<td valign="top">Custody can be upgraded without any product changing a call; the mode is reported and tested rather than assumed.</td>
<td valign="top"><code>pdi/<wbr>hosting.py</code> — <code>test_<wbr>hosting.py</code>,<br><code>test_<wbr>hosting_<wbr>modes.py</code>,<br><code>test_<wbr>byok.py</code></td>
</tr>
<tr>
<td valign="top">4</td>
<td valign="top">Access granted in advance for a person's absence is a credential that exists now, and a credential that exists can be used now.</td>
<td valign="top">A <strong>bequest</strong> names a grantee, a bounded set of key scopes and a condition, and <strong>no credential exists until the condition is attested</strong>: the grant token is minted at activation by the operator against a mandatory attestation reference recorded in the audit chain; it is read-only, bounded to its scopes, revocable, and a customer-held key stays part of the estate.</td>
<td valign="top">A dormant bequest cannot be exercised, stolen or guessed, because there is nothing to steal; activation leaves an audit entry naming what was attested.</td>
<td valign="top"><code>pdi/<wbr>bequests.py</code> — <code>test_<wbr>bequests.py</code>,<br><code>test_<wbr>the_<wbr>grant_<wbr>outlived_<wbr>the_<wbr>vault.py</code></td>
</tr>
<tr>
<td valign="top">6</td>
<td valign="top">A profile whose owner cannot authorize anything has no way to change hands, and an unwatched profile keeps acting in the owner's name.</td>
<td valign="top">Succession is <strong>gated by a reviewer holding a verification reference</strong> rather than the owner's token; with no named successor the profile sunsets to a frozen memorial; the same attestation reference joins the guardian's silence vigil (JIM-mini) and the vault's bequest activation (PDI).</td>
<td valign="top">One attested event carries a person's absence through all three products, and a profile is never an orphan that keeps posting.</td>
<td valign="top"><code>pdi/<wbr>acceptance.py</code>,<br><code>pdi/<wbr>transfers.py</code> — <code>test_<wbr>transfers.py</code>,<br><code>test_<wbr>a_<wbr>guarantee_<wbr>nobody_<wbr>reruns_<wbr>is_<wbr>marketing.py</code>; QRME <code>test_<wbr>memorial.py</code></td>
</tr>
<tr>
<td valign="top">—</td>
<td valign="top">A journal of what was done to a tenant's records is a second way to read those records, and a second door is a door the audit does not see.</td>
<td valign="top">The operations journal is <strong>a view over the ordinary audited decryption path</strong>: every journal entry is read exactly as a direct read would be, so each journal read lands on the tamper-evident hash-chained audit log.</td>
<td valign="top">The journal adds no door; reading the journal is itself in the journal.</td>
<td valign="top"><code>pdi/<wbr>audit.py</code>,<br><code>GET /<wbr>operations</code> — <code>test_<wbr>operations.py</code></td>
</tr>
</tbody>
</table>

## Where each highlight is proven

Each row: the technical problem, the implementation with its own numbers, the test that holds it, and the photograph.

| Highlight | The technical problem | As built, with its numbers | Test | Screen |
|---|---|---|---|---|
| Nothing leaves the host | A privacy promise made in prose leaks through one forgotten HTTP call. | `pdi/offline.py` refuses every non-loopback connect at the socket layer while the gate is up. | `test_nothing_leaves_the_host.py` | 09 |
| Keys rotate and retire; retention is stated and swept | A key that never rotates is a key whose compromise is permanent; a retention promise nobody sweeps is a sentence. | `pdi/crypto.py` seals each record under AES-256-GCM with a per-scope data key wrapped by the key-encryption key (12-byte nonce, the key never on a record), caches the KEK for `KEK_CACHE_SECONDS = 300`; `pdi/retention.py` keeps `WINDOWS` of 7, 30, 90, 180 and 365 days or forever and sweeps them. | `test_keymgmt_retention.py`, `test_byok.py` | 06 |
| Custody beacons and the gate | A code printed at a venue that resolves after custody changed is a leak in ink. | `pdi/beacons.py` and `pdi/gate.py` resolve a beacon only while its custody row stands; taking it down deactivates rather than deletes. | `test_beacons.py` | 12 |
| The audit chain | A log an operator can edit is a log of what the operator wanted. | `pdi/audit.py` chains every event by SHA-256 over the previous hash from a 64-zero genesis; a changed row breaks every hash after it. | `test_a_guarantee_nobody_reruns_is_marketing.py` | 05 |
| The resident answers from sealed records | A model that answers from its training answers about somebody else. | `pdi/resident.py` runs inference inside the vault's own process over decrypted records that never leave it. | `test_the_resident_learns_from_the_corpus.py` | 20 |
| The capture grows ears | A vault that keeps only text loses what was said. | `pdi/ears.py` turns audio and video into words on the deployment's own machine before sealing. | `test_the_capture_grows_ears.py` | 20 |
| The position and assistant builder | An assistant with no stated position answers from whoever asked last. | `pdi/positions.py` keeps a position as rows the assistant is built from and cites. | `test_positions.py` | 17 |
| Another tenant's shelf stays theirs | One SQL path without a tenant clause is every tenant's data. | `pdi/vault.py` scopes every query by tenant; the guard reads every SQL path in the tree. | `test_the_other_tenants_shelf.py`, `test_one_tenant_cannot_read_another.py` | 04 |
| Bequests that begin at attestation | A credential granted in advance exists now. | `pdi/bequests.py` mints the grant only on `CONDITIONS` of `executor` or `attestation`, read-only, scoped, and refused once the vault is closed. | `test_bequests.py`, `test_the_grant_outlived_the_vault.py` | 15 |
| Ability is not a gate | A screen that needs a mouse locks out the person the vault belongs to. | `app/` exposes every control to keyboard and reader; the guard reads the markup. | `test_ability_is_not_a_gate.py` | 19 |

