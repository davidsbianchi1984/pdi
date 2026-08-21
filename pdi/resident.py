"""The resident intelligence: the agent living in this process, beside the data.

The stack's three products talk to each other over HTTP, and for most people
that is the right shape — a phone in a pocket has no business hosting an
inference engine. But PDI's whole offer is a **place where the bytes live**
(`hosting.py`: our facility, leased space, your facility, your own device),
and for a tenant whose vault sits in a colocation rack or their own data
centre, shipping every question across a network to a separate orchestration
service is backwards: the data has gravity, and the intelligence should live
where it lives.

So this module is that opposite approach: **the database made smart, in one
process**. No queue, no sidecar, no orchestration service — the planner, the
tool registry, the table writer, the embedder and the local model call all
run inside the same process that holds the vault, behind the same tenant
fence the isolation guard just closed, writing the same audit chain. The
HTTP doors in `api.py` are the same engine reached from outside, which is
what keeps the promise symmetrical: a tenant who does not opt into a
facility gets the identical privacy through the standard service, because
there is only one code path to get it from.

    asked     can the coach and agent run beside the data
    mattered  does anything leave the building to make them work

## What it does, in five sentences

**It plans multi-step tasks.** A goal in words becomes ordered steps, each
naming a tool from the closed registry below; the plan is rows in
``resident_tasks``/``resident_steps``, inspectable before and after it runs.

**It calls tools through one registry.** :data:`TOOLS` is the whole
vocabulary — fetch, seal, tabulate, embed, search, infer. A plan naming a
tool that is not on it refuses at planning time, not at three a.m.

**It uses local inference only.** ``infer.local`` reaches an inference
server on *this* host (`PDI_OLLAMA_URL`) or answers with the honest stub —
never a cloud model, because a resident that phones out is not resident.
The planner itself is deterministic rules, so the plan is explainable and
identical with no model installed; a model here is a voice, not a decider,
which is `gate.py`'s rule arriving one layer down.

**It writes structured results into tables the app can query.**
``table.append`` validates flat rows into a named dataset in
``resident_rows`` — and can derive rows from the text a previous fetch
step brought home, which is the whole errand in one plan: fetch data,
put it in a table, query it.

**It embeds for vector search.** ``embed.text`` stores an L2-normalised
vector per key; ``search.vectors`` ranks by cosine. With a local model the
embedder is that model; without one it is a deterministic hashed n-gram
embedding — labelled, because vectors from two embedders do not share a
space and pretending otherwise ranks garbage confidently.

## The privacy posture

Fetched content is sealed into the vault (AES-256-GCM, AAD-bound) and steps
carry the *reference*; dataset rows are queryable on purpose — that is what
a table is for — and the door that writes them is the tenant's own token.
Vectors store a hash of the text, never the text. Every task, step and
fetch lands on the audit chain. And every statement below carries
``tenant_id`` in the SQL, because this module was born after the isolation
round and has no excuse.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
import urllib.request
from datetime import datetime, timedelta, timezone

from . import audit, db, hosting, i18n, offline, vault

#: The embedding this module can always produce: tokens and their character
#: trigrams hashed into a fixed-width space, signed, accumulated and
#: L2-normalised. Deterministic, offline, dependency-free — and honest about
#: being a lexical embedding, not a semantic one.
HASHED_EMBEDDER = "hashed-ngram-v1"
HASHED_DIM = 256

#: How much fetched text is kept. A page is sealed for reading back, not for
#: archiving the internet.
MAX_FETCH_BYTES = 512 * 1024

#: Steps per task and rows per append — ceilings, because an engine living
#: beside the vault must not be able to eat the host it lives on.
MAX_STEPS = 20
MAX_ROWS_PER_APPEND = 500
MAX_COLUMNS = 64

#: How many past cycles a task's runs ledger keeps. The ledger answers
#: "lately", not "ever" — the audit chain is the permanent record.
RUNS_KEPT = 200

_DATASET = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class ResidentError(ValueError):
    """A refusal in a sentence the caller can act on."""


class ResidentStateError(ResidentError):
    """The task exists and is not in a runnable state — a conflict, not a
    missing thing, and the route answers 409 rather than 404 by catching
    this type instead of reading the sentence."""


# --------------------------------------------------------------------------
# local inference — this host or nobody
# --------------------------------------------------------------------------

def _ollama_url() -> str | None:
    """The local inference server, if the operator pointed at one.

    Only read from the environment, never defaulted to a port probe: a
    resident that scans localhost for services is indistinguishable from
    malware to the operator watching it.
    """
    return os.environ.get("PDI_OLLAMA_URL") or None


def local_model() -> str | None:
    return os.environ.get("PDI_RESIDENT_MODEL") or (
        "llama3.2" if _ollama_url() else None)


def model_standing() -> dict | None:
    """Whether the configured inference server actually answers — proven,
    not read off the environment.

    `posture` used to report `local_model` alone, which is the *promise*:
    the name an operator wrote into `PDI_RESIDENT_MODEL`. Between that
    promise and an answer sit the two failures the deploy runbook's §8
    actually produces — the daemon is down (or on the wrong network), or
    the daemon is up and the model was never pulled — and neither was
    visible anywhere until an ask failed mid-conversation with a raw
    socket error.

    One cheap round trip settles both: Ollama's `/api/tags` lists what is
    pulled, so reaching it proves the daemon and reading it proves the
    model. `None` when no server is configured — the stub posture is not
    a failure and gets no diagnosis. Never raises: this feeds a posture
    read, and a status door that can take its page down is a status door
    pointed the wrong way.
    """
    url = _ollama_url()
    if not url:
        return None
    model = local_model()
    try:
        offline.allow(url, "local inference")
        req = urllib.request.Request(url.rstrip("/") + "/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:  # local only
            body = json.loads(resp.read().decode("utf-8"))
        pulled = [str(m.get("name", "")) for m in body.get("models", [])]
        # Ollama names carry a tag ("llama3.2:1b"); a configured name
        # without one matches its ":latest" row.
        here = any(p == model or p.split(":")[0] == model for p in pulled)
        return {"reachable": True, "model": model, "pulled": here,
                "note": None if here else
                (f"the server answers but {model!r} is not pulled — "
                 f"run: ollama pull {model}")}
    except Exception as exc:  # noqa: BLE001 — the diagnosis IS the catch
        return {"reachable": False, "model": model, "pulled": False,
                "note": (f"the inference server at PDI_OLLAMA_URL did not "
                         f"answer ({exc}) — check the ollama container is "
                         "running and on this stack's network")}


def infer(prompt: str) -> dict:
    """One local turn. The stub is an answer, not an apology: a facility
    with no model installed still gets a working engine, and the sentence
    says exactly which kind answered."""
    url = _ollama_url()
    if not url:
        return {"model": "stub",
                "text": ("No local model is installed on this host. The "
                         "resident engine plans, fetches, tabulates and "
                         "searches without one; install a local inference "
                         "server and set PDI_OLLAMA_URL to add generation.")}
    offline.allow(url, "local inference")
    req = urllib.request.Request(
        url.rstrip("/") + "/api/generate",
        data=json.dumps({"model": local_model(), "prompt": prompt,
                         "stream": False}).encode(),
        headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # localhost only
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — the sentence names it
        # A configured server that does not answer used to raise a raw
        # socket error out of the ask door, mid-conversation, through
        # whichever tandem routed here. The honest turn says what failed
        # and what still works, and the model field marks it so a
        # tandem's answered-by line never claims the local model spoke.
        return {"model": "local-unreachable",
                "text": (f"The local inference server did not answer "
                         f"({exc}). The resident's other tools — search, "
                         "tables, fetch, the vault — still work; check "
                         "the ollama container and the pulled model, or "
                         "clear PDI_OLLAMA_URL to use the stub.")}
    return {"model": f"local:{local_model()}", "text": body.get("response", "")}


def ask(tenant: dict, prompt: str) -> dict:
    """One direct local turn for this tenant — the tandems' voice door.

    `infer.local` already answers inside a plan; this is the same engine
    behind a single door, so a tandem can put the vault's own model in
    its provider registry and a profile or coach can *speak* from inside
    the facility — the prompt reaches only this host's inference server
    and never leaves it. The audit line carries the prompt's length,
    never its words: an inference ledger that quoted prompts would be a
    transcript of everything private the tandems route here.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ResidentError(
            "say something to ask — an empty prompt generates nothing")
    out = infer(prompt[:8000])
    audit.record("resident.infer", tenant_id=tenant["id"],
                 ref=f"chars:{len(prompt)}")
    return {"model": out["model"], "text": out["text"],
            "leaves_host": False}


def _grounding_text(value: str) -> str:
    """The readable heart of a sealed record: memory seals carry `line`,
    captures carry `text`; a plain string grounds as itself."""
    try:
        data = json.loads(value)
    except ValueError:
        return value.strip()
    if isinstance(data, dict):
        return str(data.get("line") or data.get("text") or "").strip()
    return ""


def ask_grounded(tenant: dict, question: str, top_k: int = 4,
                 prefix: str | None = None,
                 system: str | None = None) -> dict:
    """An answer drawn from what the vault holds — search, read, infer,
    all inside this host.

    The voice door answers from the model's own priors; this one retrieves
    first: the question ranks the tenant's vectors, the matched keys' seals
    are read back, and the local model answers *from* them — the smart
    database's whole promise in one door, with nothing leaving the host.
    `drew_on` names the keys, because an answer that will be relied on
    should say what it stood on — and an empty list is said, not padded:
    a vault that holds nothing relevant answers ungrounded and admits it.
    The audit line counts characters and keys and quotes neither the
    question nor the seals.

    `prefix` narrows what may ground the answer to keys under it — a
    character compare like `forget`'s, never a LIKE wildcard — for the
    tandems, whose one tenant holds many people's seals: Alice's question
    must never ground on Bob's memories. `system` rides ahead of the
    grounding block so a persona survives being grounded; retrieval ranks
    only the question.
    """
    question = (question or "").strip()
    if not question:
        raise ResidentError(
            "say something to ask — an empty prompt generates nothing")
    top_k = max(1, min(int(top_k), 10))
    # Over-fetch when scoping: the prefix filter discards other people's
    # keys after ranking, and one person's nearest moments may sit behind
    # many strangers' in the tenant-wide order.
    found = search(tenant, question,
                   top_k=top_k * 4 if prefix else top_k)
    drew_on, context = [], []
    for m in found.get("matches", []):
        if prefix and m["key"][:len(prefix)] != prefix:
            continue
        if len(drew_on) >= top_k:
            break
        rec = vault.get(tenant, m["key"])
        if rec is None:
            # A vector whose seal is gone grounds nothing: the index knows
            # a direction, and a direction alone is not evidence.
            continue
        text = _grounding_text(rec["value"])
        if not text:
            continue
        drew_on.append(m["key"])
        context.append(f"[{m['key']}] {text[:500]}")
    if context:
        prompt = ("Answer from what this vault holds. Sealed records, "
                  "nearest the question first:\n" + "\n".join(context)
                  + "\n\nQuestion: " + question + "\nAnswer: ")
    else:
        prompt = question
    if system:
        prompt = system.strip() + "\n\n" + prompt
    out = infer(prompt[:8000])
    audit.record("resident.ask", tenant_id=tenant["id"],
                 ref=f"chars:{len(question)} keys:{len(drew_on)}")
    return {"model": out["model"], "text": out["text"],
            "leaves_host": False, "drew_on": drew_on}


# --------------------------------------------------------------------------
# embeddings — one space per embedder, and the label travels with the vector
# --------------------------------------------------------------------------

def _hashed_embedding(text: str) -> list[float]:
    vec = [0.0] * HASHED_DIM
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    grams = [t[i:i + 3] for t in tokens for i in range(max(len(t) - 2, 1))]
    for piece in tokens + grams:
        h = hashlib.sha256(piece.encode()).digest()
        at = int.from_bytes(h[:4], "little") % HASHED_DIM
        sign = 1.0 if h[4] % 2 else -1.0
        vec[at] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _model_embedding(text: str) -> tuple[str, list[float]] | None:
    url = _ollama_url()
    if not url:
        return None
    model = os.environ.get("PDI_EMBED_MODEL", "nomic-embed-text")
    offline.allow(url, "a local embedding")
    req = urllib.request.Request(
        url.rstrip("/") + "/api/embeddings",
        data=json.dumps({"model": model, "prompt": text}).encode(),
        headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # localhost only
        body = json.loads(resp.read().decode("utf-8"))
    raw = body.get("embedding") or []
    if not raw:
        return None
    norm = math.sqrt(sum(v * v for v in raw)) or 1.0
    return f"local:{model}", [v / norm for v in raw]


def embed(tenant: dict, key: str, text: str) -> dict:
    """Embed and store. Replaces the vector under the same key — an index
    holds the current text, and the audit chain holds that it changed."""
    text = (text or "").strip()
    if not text:
        raise ResidentError("nothing to embed — say a few words first")
    made = _model_embedding(text)
    embedder, vec = made if made else (HASHED_EMBEDDER, _hashed_embedding(text))
    blob = struct.pack(f"<{len(vec)}f", *vec)
    conn = db.connect()
    conn.execute(
        "DELETE FROM resident_vectors WHERE tenant_id=? AND key=?",
        (tenant["id"], key))
    conn.execute(
        "INSERT INTO resident_vectors (id, tenant_id, key, text_sha256,"
        " embedder, dim, vector, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (db.new_id("vec"), tenant["id"], key,
         hashlib.sha256(text.encode()).hexdigest(), embedder, len(vec),
         blob, db.utcnow()))
    conn.commit()
    audit.record("resident.embed", tenant_id=tenant["id"], ref=key)
    return {"key": key, "embedder": embedder, "dim": len(vec),
            "note": "the vector is stored; the text is not"}


def forget(tenant: dict, key: str, prefix: bool = False) -> dict:
    """Remove vectors — one key, or everything under it as a prefix.

    The other half of `embed`, and the half erasure stands on. A vector
    stores a hash and a direction, not the words — but a direction still
    ranks, and a memory somebody deleted must stop being findable, not
    merely stop being readable. Prefix mode exists for the tandems' erasure
    sweeps: a person's memories go in one call, not one round-trip per
    moment they ever had.
    """
    key = (key or "").strip()
    if not key:
        raise ResidentError("forgetting needs a key")
    conn = db.connect()
    if prefix:
        # `substr`, not LIKE: keys legitimately carry underscores, which are
        # LIKE wildcards, and SQLite honors an escape only with an ESCAPE
        # clause. A character-for-character prefix compare has no wildcard
        # semantics to defend against.
        removed = conn.execute(
            "DELETE FROM resident_vectors WHERE tenant_id=?"
            " AND substr(key, 1, ?) = ?",
            (tenant["id"], len(key), key)).rowcount
    else:
        removed = conn.execute(
            "DELETE FROM resident_vectors WHERE tenant_id=? AND key=?",
            (tenant["id"], key)).rowcount
    conn.commit()
    audit.record("resident.forget", tenant_id=tenant["id"],
                 ref=f"{key}{'*' if prefix else ''}:{removed}")
    return {"key": key, "prefix": prefix, "vectors_removed": removed}


def search(tenant: dict, query: str, top_k: int = 5) -> dict:
    """Cosine over this tenant's vectors, within one embedder's space.

    The query is embedded the same way the majority of the index was, and
    only vectors from that embedder are ranked — two embedders' vectors do
    not share a space, and mixing them ranks noise with confidence.
    """
    query = (query or "").strip()
    if not query:
        raise ResidentError("nothing to search for — say a few words first")
    top_k = max(1, min(int(top_k), 50))
    rows = db.connect().execute(
        "SELECT key, embedder, dim, vector FROM resident_vectors"
        " WHERE tenant_id=?", (tenant["id"],)).fetchall()
    if not rows:
        return {"query": query, "matches": [], "embedder": None,
                "note": "no vectors yet — embed something first"}
    spaces: dict[str, int] = {}
    for r in rows:
        spaces[r["embedder"]] = spaces.get(r["embedder"], 0) + 1
    space = max(spaces, key=lambda k: spaces[k])
    if space == HASHED_EMBEDDER:
        qvec = _hashed_embedding(query)
    else:
        made = _model_embedding(query)
        if made is None or made[0] != space:
            raise ResidentError(
                i18n.fill(i18n.RESIDENT_LOST_SPACE, space=space))
        qvec = made[1]
    scored = []
    for r in rows:
        if r["embedder"] != space:
            continue
        vec = struct.unpack(f"<{r['dim']}f", r["vector"])
        scored.append((sum(a * b for a, b in zip(qvec, vec)), r["key"]))
    scored.sort(reverse=True)
    return {"query": query, "embedder": space,
            "matches": [{"key": k, "score": round(s, 4)}
                        for s, k in scored[:top_k]],
            "skipped_other_spaces": len(rows) - len(scored)}


# --------------------------------------------------------------------------
# tables — structured results the app can query
# --------------------------------------------------------------------------

def _clean_rows(rows: list) -> list[dict]:
    if not isinstance(rows, list) or not rows:
        raise ResidentError("rows must be a non-empty list of flat objects")
    if len(rows) > MAX_ROWS_PER_APPEND:
        raise ResidentError(
            i18n.fill(i18n.RESIDENT_MAX_ROWS, n=MAX_ROWS_PER_APPEND))
    out = []
    for row in rows:
        if not isinstance(row, dict) or not row:
            raise ResidentError("every row must be a non-empty object")
        if len(row) > MAX_COLUMNS:
            raise ResidentError(i18n.fill(i18n.RESIDENT_MAX_COLUMNS, n=MAX_COLUMNS))
        for k, v in row.items():
            if not isinstance(k, str) or not _DATASET.match(k):
                raise ResidentError(
                    i18n.fill(i18n.RESIDENT_BAD_COLUMN, name=repr(k)))
            if not (v is None or isinstance(v, (str, int, float, bool))):
                raise ResidentError(
                    i18n.fill(i18n.RESIDENT_NESTED_COLUMN, name=repr(k)))
        out.append(row)
    return out


def append_rows(tenant: dict, dataset: str, rows: list,
                source_ref: str | None = None) -> dict:
    if not _DATASET.match(dataset or ""):
        raise ResidentError(
            "dataset names are lower-case letters, digits and underscores, "
            "starting with a letter")
    clean = _clean_rows(rows)
    conn = db.connect()
    now = db.utcnow()
    for row in clean:
        conn.execute(
            "INSERT INTO resident_rows (id, tenant_id, dataset, row,"
            " source_ref, created_at) VALUES (?,?,?,?,?,?)",
            (db.new_id("row"), tenant["id"], dataset,
             json.dumps(row, sort_keys=True), source_ref, now))
    conn.commit()
    audit.record("resident.rows", tenant_id=tenant["id"],
                 ref=f"{dataset}:{len(clean)}")
    return {"dataset": dataset, "appended": len(clean)}


def datasets(tenant: dict) -> list[dict]:
    rows = db.connect().execute(
        "SELECT dataset, COUNT(*) AS n, MAX(created_at) AS last"
        " FROM resident_rows WHERE tenant_id=? GROUP BY dataset"
        " ORDER BY dataset", (tenant["id"],)).fetchall()
    return [{"dataset": r["dataset"], "row_count": r["n"],
             "last_write": r["last"]}
            for r in rows]


def read_rows(tenant: dict, dataset: str, limit: int = 100) -> dict:
    limit = max(1, min(int(limit), 1000))
    rows = db.connect().execute(
        "SELECT row, source_ref, created_at FROM resident_rows"
        " WHERE tenant_id=? AND dataset=? ORDER BY created_at, rowid"
        " LIMIT ?", (tenant["id"], dataset, limit)).fetchall()
    return {"dataset": dataset,
            "dataset_rows": [{**json.loads(r["row"]),
                      "_source": r["source_ref"], "_at": r["created_at"]}
                     for r in rows]}


# --------------------------------------------------------------------------
# tools — the closed registry
# --------------------------------------------------------------------------

def _fetch_text(url: str) -> str:
    """One trip out, past the offline gate, text back. Split out so a test
    can stand in for the network without standing in for the rules."""
    offline.allow(url, "a resident fetch")
    req = urllib.request.Request(url, headers={"user-agent": "pdi-resident"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read(MAX_FETCH_BYTES)
    text = raw.decode("utf-8", errors="replace")
    # Markup stripped to what a reader reads; the engine tabulates text,
    # it does not archive pages.
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text,
                  flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _prior_capture(tenant: dict, key: str) -> dict | None:
    """The seal this fetch is about to overwrite, if it parses — so a
    re-fetch can say whether the page actually changed rather than only
    that it was fetched again."""
    try:
        rec = vault.get(tenant, key)
    except Exception:  # noqa: BLE001 — a lost prior is a first capture
        return None
    if rec is None:
        return None
    try:
        prior = json.loads(rec["value"])
    except (KeyError, TypeError, ValueError):
        return None
    return prior if isinstance(prior, dict) else None


def _capture_sha(sealed: dict) -> str | None:
    """A capture's fingerprint — its own when it carries one, derived
    from its text when it predates fingerprints, so an identical page is
    never reported changed just because the seal got a new field."""
    if sealed.get("sha"):
        return sealed["sha"]
    text = sealed.get("text")
    if not isinstance(text, str):
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _seal_capture(tenant: dict, ctx: dict, url: str, text: str,
                  extra: dict | None = None) -> tuple[str, str]:
    """Seal one capture and say what changed. Shared by the plain fetch and
    the rendered one, so both kinds of reading keep the same memory: the
    fingerprint is what lets the seal remember *when the page last actually
    changed* across a standing fetch's overwrites, not merely when it was
    last read."""
    key = f"resident/{ctx['task_id']}/{ctx['position']:02d}-fetch"
    now = db.utcnow()
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    prior = _prior_capture(tenant, key)
    if prior is not None and _capture_sha(prior) == sha:
        # A prior from before fingerprints has no changed_at; the honest
        # stand-in is its own fetch time — the page has held at least
        # that long — never `now`, which would invent a fresh change.
        changed_at = (prior.get("changed_at") or prior.get("fetched_at")
                      or now)
        note = "unchanged"
    else:
        changed_at = now
        note = "changed" if prior is not None else "first capture"
    first_seen_at = ((prior or {}).get("first_seen_at")
                     or (prior or {}).get("fetched_at") or now)
    seal = {"url": url, "text": text, "fetched_at": now, "sha": sha,
            "changed_at": changed_at, "first_seen_at": first_seen_at}
    seal.update(extra or {})
    vault.put(tenant, key, json.dumps(seal))
    ctx["last_text"], ctx["last_source"] = text, url
    return key, note


def _refuse_a_recording(url: str, tool: str) -> None:
    """The reading tools do not read recordings. A plain fetch of an .mp4
    strips markup from compressed video and seals mojibake as a capture —
    the exact defect the ears were built against, still open on the direct
    doors after the planner learned to route media to `fetch.listen`. The
    refusal names that door, because "I cannot" without "here is what can"
    is the menu problem inside a tool registry."""
    from . import ears
    if ears.looks_like_recording(url):
        raise ResidentError(
            f"{tool} reads pages, and that url names a recording — "
            "fetch.listen is the door that hears it")


def _tool_fetch(tenant: dict, args: dict, ctx: dict) -> dict:
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ResidentError("fetch.url needs an http(s) url")
    _refuse_a_recording(url, "fetch.url")
    text = _fetch_text(url)
    key, note = _seal_capture(tenant, ctx, url, text)
    audit.record("resident.fetch", tenant_id=tenant["id"], ref=url)
    return {"result_ref": key,
            "summary": f"fetched {len(text)} chars, sealed at {key}"
                       f" ({note})"}


def _tool_fetch_render(tenant: dict, args: dict, ctx: dict) -> dict:
    """The capture with eyes: the page rendered as a person meets it.

    A JavaScript application answers a plain fetch with an empty shell and
    a title — a dozen characters standing where a whole console is — so
    this tool asks the deployment's rendering sidecar (pdi/renderer.py)
    instead. A deployment without the sidecar, or whose sidecar fails,
    falls back to the plain fetch **and the seal says so**: `rendered` is
    the honest column, and `render_fallback` carries the reason. An honest
    shell beats a silent one — the lookout reading this capture can tell
    the difference between "the page says little" and "we could not see".
    """
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ResidentError("fetch.url needs an http(s) url")
    _refuse_a_recording(url, "fetch.render")
    from . import renderer
    rendered, fallback = True, None
    try:
        text = renderer.render_text(url)
    except renderer.RendererUnavailable as exc:
        text = _fetch_text(url)
        rendered, fallback = False, str(exc)
    extra: dict = {"rendered": rendered}
    if fallback:
        extra["render_fallback"] = fallback
    key, note = _seal_capture(tenant, ctx, url, text, extra)
    audit.record("resident.fetch", tenant_id=tenant["id"], ref=url)
    how = "rendered" if rendered else f"plain fetch stood in: {fallback}"
    return {"result_ref": key,
            "summary": f"fetched {len(text)} chars ({how}), sealed at {key}"
                       f" ({note})"}


def _tool_fetch_listen(tenant: dict, args: dict, ctx: dict) -> dict:
    """The capture with ears: a recording turned into the words said in it.

    The deployment's transcription sidecar (pdi/ears.py) downloads the
    audio or video and runs a local speech-to-text model; what gets sealed
    is the words — the same capture shape and change-memory the fetches
    keep, so a standing listen notices when a recording's words change.

    Unlike the eyes there is no honest stand-in: the shell of a page is
    still the page's text, but the bytes of a recording are not its words.
    A deployment without ears, or whose ears fail, fails the step in words
    — the runs ledger carries the reason, and the lookout's `trouble` line
    can say it — rather than sealing silence or bytes as a transcript.
    """
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ResidentError("fetch.listen needs an http(s) url")
    from . import ears
    try:
        heard = ears.transcribe(url)
    except ears.EarsUnavailable as exc:
        raise ResidentError(f"the vault has no ears for this: {exc}")
    extra: dict = {"transcribed": True}
    if heard.get("duration_seconds") is not None:
        extra["duration_seconds"] = heard["duration_seconds"]
    if heard.get("language"):
        extra["language"] = heard["language"]
    key, note = _seal_capture(tenant, ctx, url, heard["text"], extra)
    audit.record("resident.fetch", tenant_id=tenant["id"], ref=url)
    return {"result_ref": key,
            "summary": f"heard {len(heard['text'])} chars (transcribed), "
                       f"sealed at {key} ({note})"}


def _tool_vault_put(tenant: dict, args: dict, ctx: dict) -> dict:
    key = (args.get("key") or "").strip()
    value = args.get("value")
    if not key or value is None:
        raise ResidentError("vault.put needs a key and a value")
    vault.put(tenant, key, str(value))
    return {"result_ref": key, "summary": f"sealed at {key}"}


def _tool_vault_get(tenant: dict, args: dict, ctx: dict) -> dict:
    key = (args.get("key") or "").strip()
    rec = vault.get(tenant, key)
    if rec is None:
        raise ResidentError(i18n.fill(i18n.RESIDENT_NOTHING_SEALED, key=key))
    ctx["last_text"], ctx["last_source"] = str(rec["value"]), key
    return {"result_ref": key, "summary": f"read {key}"}


def _derived_rows(args: dict, ctx: dict) -> tuple[list[dict], str | None]:
    """Rows straight from the caller, or derived from the last fetched text —
    the fetch → table pipeline in one plan, deterministically."""
    if args.get("rows") is not None:
        return args["rows"], args.get("source_ref")
    how = args.get("derive")
    text = ctx.get("last_text")
    if how is None or text is None:
        raise ResidentError(
            "table.append needs rows, or derive:'lines'|'csv' after a fetch")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if how == "lines":
        return ([{"n": i + 1, "line": ln[:2000]}
                 for i, ln in enumerate(lines[:MAX_ROWS_PER_APPEND])],
                ctx.get("last_source"))
    if how == "csv":
        if len(lines) < 2:
            raise ResidentError("csv derivation needs a header line and rows")
        head = [h.strip() or f"col{i}" for i, h in
                enumerate(lines[0].split(","))]
        out = []
        for ln in lines[1:MAX_ROWS_PER_APPEND + 1]:
            cells = [c.strip() for c in ln.split(",")]
            out.append({(head[i] if _DATASET.match(head[i]) else f"col{i}"):
                        cells[i] if i < len(cells) else None
                        for i in range(len(head))})
        return out, ctx.get("last_source")
    raise ResidentError(i18n.fill(i18n.RESIDENT_BAD_DERIVE, how=repr(how)))


def _tool_table_append(tenant: dict, args: dict, ctx: dict) -> dict:
    dataset = args.get("dataset") or ""
    rows, source = _derived_rows(args, ctx)
    out = append_rows(tenant, dataset, rows, source_ref=source)
    return {"result_ref": dataset,
            "summary": f"{out['appended']} row(s) into {dataset}"}


def _tool_embed(tenant: dict, args: dict, ctx: dict) -> dict:
    text = args.get("text") or ctx.get("last_text")
    key = (args.get("key") or "").strip()
    if not key:
        raise ResidentError("embed.text needs a key")
    if not text:
        raise ResidentError("embed.text needs text, or a fetch before it")
    out = embed(tenant, key, str(text))
    return {"result_ref": key,
            "summary": f"embedded as {key} ({out['embedder']})"}


def _tool_search(tenant: dict, args: dict, ctx: dict) -> dict:
    out = search(tenant, args.get("query") or "", int(args.get("top_k") or 5))
    ctx["last_text"] = json.dumps(out["matches"])
    return {"result_ref": None,
            "summary": f"{len(out['matches'])} match(es) for "
                       f"{out['query']!r}"}


def _tool_infer(tenant: dict, args: dict, ctx: dict) -> dict:
    prompt = args.get("prompt") or ctx.get("last_text") or ""
    if not prompt:
        raise ResidentError("infer.local needs a prompt, or a step before it")
    out = infer(str(prompt)[:8000])
    key = f"resident/{ctx['task_id']}/{ctx['position']:02d}-inference"
    vault.put(tenant, key, json.dumps(out))
    ctx["last_text"] = out["text"]
    return {"result_ref": key,
            "summary": f"{out['model']} answered; sealed at {key}"}


#: The whole vocabulary. `leaves_host` is the honest column: the registry is
#: published on GET /resident, and a tenant deciding whether to run a plan
#: should not have to read Python to learn which steps go outside.
TOOLS: dict[str, dict] = {
    "fetch.url": {"means": "fetch a page's text and seal it in the vault",
                  "leaves_host": True, "run": _tool_fetch},
    "fetch.render": {"means": "fetch a page as a person sees it — rendered "
                              "in the deployment's browser — and seal it; "
                              "the plain fetch stands in, and the seal says "
                              "so, when no renderer is deployed",
                     "leaves_host": True, "run": _tool_fetch_render},
    "fetch.listen": {"means": "fetch a recording and seal the words said "
                              "in it — transcribed by the deployment's "
                              "ears; a deployment without ears refuses in "
                              "words rather than sealing silence or bytes",
                     "leaves_host": True, "run": _tool_fetch_listen},
    "vault.put": {"means": "seal a value in the vault",
                  "leaves_host": False, "run": _tool_vault_put},
    "vault.get": {"means": "read a sealed value back",
                  "leaves_host": False, "run": _tool_vault_get},
    "table.append": {"means": "write flat rows into a queryable dataset",
                     "leaves_host": False, "run": _tool_table_append},
    "embed.text": {"means": "store an embedding for vector search",
                   "leaves_host": False, "run": _tool_embed},
    "search.vectors": {"means": "rank this tenant's vectors by cosine",
                       "leaves_host": False, "run": _tool_search},
    "infer.local": {"means": "one turn of local inference (or the honest "
                             "stub when no model is installed)",
                    "leaves_host": False, "run": _tool_infer},
}


# --------------------------------------------------------------------------
# the planner — deterministic rules; a model is a voice, not a decider
# --------------------------------------------------------------------------

_URL = re.compile(r"https?://\S+")
# "into table prices" — the noise word between the verb and the name is
# skipped, so the dataset is `prices`, not `table`.
_DATASET_WORD = re.compile(
    r"\b(?:into|table|dataset)\s+(?!table\b)([a-z][a-z0-9_]{0,63})")
_KEY_WORD = re.compile(r"\b(?:as|key)\s+([\w/.\-]+)")


def _step_from(fragment: str) -> dict:
    """One fragment of a goal to one tool call, by its verbs. Deterministic
    and explainable: the plan can be read before it runs, and reads the same
    on a host with no model at all."""
    low = fragment.lower()
    url = _URL.search(fragment)
    if url and any(w in low for w in ("listen", "transcribe", "hear")):
        # "listen" (or "transcribe", "hear") asks for the words said in a
        # recording — the ears tool, which refuses in words on a
        # deployment without them. Checked before the fetch verbs so
        # "fetch and transcribe <url>" hears rather than reads.
        return {"title": fragment, "tool": "fetch.listen",
                "args": {"url": url.group().rstrip(".,)")}}
    if url and any(w in low for w in ("fetch", "get", "read", "pull",
                                      "download", "render", "see")):
        # "render" (or "see") asks for the page as a person meets it — the
        # eyes tool, which itself says honestly when it had to stand down.
        tool = ("fetch.render" if any(w in low for w in ("render", "see"))
                else "fetch.url")
        return {"title": fragment, "tool": tool,
                "args": {"url": url.group().rstrip(".,)")}}
    if any(w in low for w in ("table", "tabulate", "rows", "dataset")):
        named = _DATASET_WORD.search(low)
        return {"title": fragment, "tool": "table.append",
                "args": {"dataset": named.group(1) if named else "results",
                         "derive": "csv" if "csv" in low else "lines"}}
    if any(w in low for w in ("embed", "index", "vector")):
        named = _KEY_WORD.search(low)
        return {"title": fragment, "tool": "embed.text",
                "args": {"key": named.group(1) if named else "latest"}}
    if "search" in low:
        return {"title": fragment, "tool": "search.vectors",
                "args": {"query": re.sub(r"^\s*search(\s+for)?\s*", "", low)}}
    if any(w in low for w in ("seal", "store", "keep")):
        named = _KEY_WORD.search(low)
        return {"title": fragment, "tool": "vault.put",
                "args": {"key": named.group(1) if named else "resident/kept",
                         "value": fragment}}
    return {"title": fragment, "tool": "infer.local",
            "args": {"prompt": fragment}}


def _decompose(goal: str) -> list[dict]:
    parts = [p.strip() for p in
             re.split(r"\bthen\b|;|\n|(?:^|\s)\d+[.)]\s", goal)
             if p and p.strip()]
    return [_step_from(p) for p in parts[:MAX_STEPS]]


def plan(tenant: dict, goal: str, steps: list[dict] | None = None,
         every_hours: float | None = None) -> dict:
    """A task planned and stored, not yet run — running is its own decision.

    Caller-supplied steps are validated against the registry exactly like
    derived ones: the registry is the boundary either way. `every_hours`
    makes it a **standing task**: the vault keeps the appointment itself
    (`pulse`), re-running the same plan on the interval — the "no separate
    orchestration service" claim extended to *when*, not just *what*.
    """
    goal = (goal or "").strip()
    if not goal:
        raise ResidentError("a task needs a goal in words")
    if every_hours is not None:
        try:
            every_hours = float(every_hours)
        except (TypeError, ValueError):
            raise ResidentError(
                "a standing task repeats on a number of hours") from None
        if not 0.25 <= every_hours <= 744:
            raise ResidentError(
                "a standing task repeats between a quarter-hour and a month")
    made = steps if steps is not None else _decompose(goal)
    if not made:
        raise ResidentError("nothing to plan — the goal decomposed to no steps")
    if len(made) > MAX_STEPS:
        raise ResidentError(i18n.fill(i18n.RESIDENT_MAX_STEPS, n=MAX_STEPS))
    for s in made:
        if s.get("tool") not in TOOLS:
            raise ResidentError(
                i18n.fill(i18n.RESIDENT_UNKNOWN_TOOL, tool=repr(s.get("tool")),
                          registry=", ".join(sorted(TOOLS))))
    conn = db.connect()
    task_id = db.new_id("rtk")
    next_run = (
        (datetime.now(timezone.utc) + timedelta(hours=every_hours)).isoformat()
        if every_hours is not None else None)
    conn.execute(
        "INSERT INTO resident_tasks (id, tenant_id, goal, planned_by,"
        " status, created_at, every_hours, next_run_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (task_id, tenant["id"], goal,
         "caller" if steps is not None else "rules-v1",
         "planned", db.utcnow(), every_hours, next_run))
    for at, s in enumerate(made, 1):
        conn.execute(
            "INSERT INTO resident_steps (id, task_id, tenant_id, position,"
            " title, tool, args, status) VALUES (?,?,?,?,?,?,?,?)",
            (db.new_id("rst"), task_id, tenant["id"], at,
             str(s.get("title") or s["tool"])[:300], s["tool"],
             json.dumps(s.get("args") or {}), "planned"))
    conn.commit()
    audit.record("resident.plan", tenant_id=tenant["id"], ref=task_id)
    return task(tenant, task_id)


def task(tenant: dict, task_id: str) -> dict:
    row = db.connect().execute(
        "SELECT * FROM resident_tasks WHERE id=? AND tenant_id=?",
        (task_id, tenant["id"])).fetchone()
    if row is None:
        raise ResidentError("no such task")
    steps = db.connect().execute(
        "SELECT * FROM resident_steps WHERE task_id=? AND tenant_id=?"
        " ORDER BY position", (task_id, tenant["id"])).fetchall()
    return {
        "id": row["id"], "goal": row["goal"], "status": row["status"],
        "planned_by": row["planned_by"], "created_at": row["created_at"],
        "finished_at": row["finished_at"],
        "every_hours": row["every_hours"],
        "next_run_at": row["next_run_at"],
        "plan_steps": [{"position": s["position"], "title": s["title"],
                   "tool": s["tool"], "args": json.loads(s["args"]),
                   "leaves_host": TOOLS[s["tool"]]["leaves_host"]
                   if s["tool"] in TOOLS else True,
                   "status": s["status"], "result_ref": s["result_ref"],
                   "summary": s["summary"], "error": s["error"]}
                  for s in steps],
    }


def tasks(tenant: dict) -> list[dict]:
    rows = db.connect().execute(
        "SELECT id FROM resident_tasks WHERE tenant_id=?"
        " ORDER BY created_at DESC, rowid DESC LIMIT 50",
        (tenant["id"],)).fetchall()
    return [task(tenant, r["id"]) for r in rows]


def run(tenant: dict, task_id: str) -> dict:
    """Execute the plan, in order, in this process. A failed step stops the
    chain and names itself; the steps after it stay `skipped`, not lied
    about."""
    current = task(tenant, task_id)
    standing = current["every_hours"] is not None
    # A standing task is *meant* to run again: `done` is a resting state,
    # not a terminal one, and its steps reset so the same plan executes
    # whole each cycle. One-shot tasks keep the stricter contract.
    if current["status"] not in ("planned", "failed") and not (
            standing and current["status"] == "done"):
        raise ResidentStateError(
            i18n.fill(i18n.RESIDENT_TASK_STATE, status=current["status"]))
    conn = db.connect()
    if standing and current["status"] == "done":
        conn.execute(
            "UPDATE resident_steps SET status='planned', result_ref=NULL,"
            " summary=NULL, error=NULL, finished_at=NULL"
            " WHERE task_id=? AND tenant_id=?", (task_id, tenant["id"]))
        conn.commit()
        current = task(tenant, task_id)
    conn.execute(
        "UPDATE resident_tasks SET status='running'"
        " WHERE id=? AND tenant_id=?", (task_id, tenant["id"]))
    conn.commit()
    ctx: dict = {"task_id": task_id}
    failed = False
    for step in current["plan_steps"]:
        if step["status"] == "done":
            continue
        position = step["position"]
        ctx["position"] = position
        if failed:
            conn.execute(
                "UPDATE resident_steps SET status='skipped'"
                " WHERE task_id=? AND tenant_id=? AND position=?",
                (task_id, tenant["id"], position))
            continue
        try:
            out = TOOLS[step["tool"]]["run"](tenant, step["args"], ctx)
            conn.execute(
                "UPDATE resident_steps SET status='done', result_ref=?,"
                " summary=?, error=NULL, finished_at=?"
                " WHERE task_id=? AND tenant_id=? AND position=?",
                (out.get("result_ref"), out.get("summary"), db.utcnow(),
                 task_id, tenant["id"], position))
        except (ResidentError, offline.LeftTheHost, OSError, ValueError,
                KeyError) as exc:
            failed = True
            conn.execute(
                "UPDATE resident_steps SET status='failed', error=?,"
                " finished_at=? WHERE task_id=? AND tenant_id=? AND position=?",
                (f"{type(exc).__name__}: {exc}"[:300], db.utcnow(),
                 task_id, tenant["id"], position))
        conn.commit()
        audit.record("resident.step", tenant_id=tenant["id"],
                     ref=f"{task_id}:{position}")
    finished_at = db.utcnow()
    conn.execute(
        "UPDATE resident_tasks SET status=?, finished_at=?"
        " WHERE id=? AND tenant_id=?",
        ("failed" if failed else "done", finished_at, task_id, tenant["id"]))
    # One ledger row per cycle, because a standing task's step rows reset
    # on the next run: without this, "what did the vault do while you
    # slept" has no answer beyond the latest state. The note is one line
    # — the failing step's error, or the last step's summary — never a
    # copy of anything sealed.
    after = task(tenant, task_id)["plan_steps"]
    note = next((s2["error"] for s2 in after if s2["status"] == "failed"),
                None) or next(
        (s2["summary"] for s2 in reversed(after)
         if s2["status"] == "done" and s2["summary"]), None)
    # The row chains to the task's previous cycle the way the audit table
    # chains deployment-wide: the hash covers the previous hash and every
    # field, so a rewritten or forged cycle breaks the links (`runs_verify`
    # walks them). The database itself refuses UPDATE on this table — a
    # ledger that can edit its own account is a diary in pencil.
    prev_row = conn.execute(
        "SELECT hash FROM resident_runs WHERE task_id=? AND tenant_id=?"
        " ORDER BY ran_at DESC, rowid DESC LIMIT 1",
        (task_id, tenant["id"])).fetchone()
    prev_hash = (prev_row["hash"] if prev_row and prev_row["hash"]
                 else RUNS_GENESIS)
    run_id = db.new_id("rrun")
    run_status = "failed" if failed else "done"
    run_note = (note or "")[:300] or None
    run_hash = _run_hash(prev_hash, {
        "id": run_id, "tenant_id": tenant["id"], "task_id": task_id,
        "ran_at": finished_at, "status": run_status, "note": run_note})
    conn.execute(
        "INSERT INTO resident_runs (id, tenant_id, task_id, ran_at, status,"
        " note, prev_hash, hash) VALUES (?,?,?,?,?,?,?,?)",
        (run_id, tenant["id"], task_id, finished_at,
         run_status, run_note, prev_hash, run_hash))
    # The ledger answers "lately", not "ever": the oldest rows beyond the
    # window go, and the audit chain stays the permanent record.
    conn.execute(
        "DELETE FROM resident_runs WHERE task_id=? AND tenant_id=?"
        " AND id NOT IN (SELECT id FROM resident_runs"
        "  WHERE task_id=? AND tenant_id=?"
        "  ORDER BY ran_at DESC, rowid DESC LIMIT ?)",
        (task_id, tenant["id"], task_id, tenant["id"], RUNS_KEPT))
    if standing:
        # The next appointment, kept whatever this cycle did: a failing
        # standing task retries on its interval rather than going silent.
        conn.execute(
            "UPDATE resident_tasks SET next_run_at=?"
            " WHERE id=? AND tenant_id=?",
            ((datetime.now(timezone.utc)
              + timedelta(hours=current["every_hours"])).isoformat(),
             task_id, tenant["id"]))
    conn.commit()
    # The cycle's anchor on the permanent chain: the run row's hash rides
    # the audit ref, so even a deleted ledger row leaves its shadow where
    # nothing edits. The ledger answers "lately"; the audit answers "ever".
    audit.record("resident.task", tenant_id=tenant["id"],
                 ref=f"{task_id}#{run_hash[:16]}")
    return task(tenant, task_id)


def cancel(tenant: dict, task_id: str) -> dict:
    """The off switch. A standing task without one is an appointment a
    tenant can make and never unmake — the beat would keep it forever.

    The task and its steps go; the audit chain and whatever the runs
    already wrote (dataset rows, sealed fetches) stay, because a cancel
    ends the future, not the record. A `running` task refuses: the run
    loop is writing step rows this delete would pull out from under it.
    """
    current = task(tenant, task_id)
    if current["status"] == "running":
        raise ResidentStateError(
            i18n.fill(i18n.RESIDENT_TASK_STATE, status=current["status"]))
    conn = db.connect()
    conn.execute("DELETE FROM resident_steps WHERE task_id=? AND tenant_id=?",
                 (task_id, tenant["id"]))
    conn.execute("DELETE FROM resident_runs WHERE task_id=? AND tenant_id=?",
                 (task_id, tenant["id"]))
    conn.execute("DELETE FROM resident_tasks WHERE id=? AND tenant_id=?",
                 (task_id, tenant["id"]))
    conn.commit()
    audit.record("resident.cancel", tenant_id=tenant["id"], ref=task_id)
    return {"id": task_id, "cancelled": True}


#: The chain's first link per task, mirroring the audit table's genesis.
RUNS_GENESIS = "runs-genesis"


def _run_hash(prev_hash: str, entry: dict) -> str:
    payload = prev_hash + json.dumps(entry, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def runs_verify(tenant: dict, task_id: str) -> dict:
    """Walk the task's ledger oldest-first and say whether it still tells
    one connected story: every chained row's hash must recompute from its
    fields, and every link must hold. The head's own `prev_hash` may point
    at a row the trim window released — the ledger answers "lately", and
    the audit chain holds every cycle's anchor forever — so the head link
    is reported, not judged. Rows minted before the chain existed are
    counted as `predate_chain`, never guessed at."""
    task(tenant, task_id)
    rows = db.connect().execute(
        "SELECT * FROM resident_runs WHERE task_id=? AND tenant_id=?"
        " ORDER BY ran_at ASC, rowid ASC", (task_id, tenant["id"])).fetchall()
    chained = [r for r in rows if r["hash"]]
    intact, prev = True, None
    for r in chained:
        entry = {"id": r["id"], "tenant_id": r["tenant_id"],
                 "task_id": r["task_id"], "ran_at": r["ran_at"],
                 "status": r["status"], "note": r["note"]}
        if _run_hash(r["prev_hash"], entry) != r["hash"]:
            intact = False
            break
        if prev is not None and r["prev_hash"] != prev:
            intact = False
            break
        prev = r["hash"]
    return {"intact": intact, "entries": len(chained),
            "predate_chain": len(rows) - len(chained),
            "window": RUNS_KEPT,
            "head_prev": chained[0]["prev_hash"] if chained else None}


def runs(tenant: dict, task_id: str) -> list[dict]:
    """The task's past cycles, newest first — the answer to "what did the
    vault do while you slept" that the resetting step rows cannot give.
    Unknown task: the same refusal every task door gives."""
    task(tenant, task_id)
    rows = db.connect().execute(
        "SELECT * FROM resident_runs WHERE task_id=? AND tenant_id=?"
        " ORDER BY ran_at DESC, rowid DESC", (task_id, tenant["id"])).fetchall()
    return [{"id": r["id"], "ran_at": r["ran_at"], "status": r["status"],
             "note": r["note"]} for r in rows]


def pulse() -> dict:
    """Run every standing task whose appointment has come — the vault's own
    heartbeat, inside the process (`PDI_RESIDENT_PULSE` starts the loop).

    Tenants first, then each tenant's due tasks: every statement that
    touches a tenant-scoped table stays constrained to one tenant, so the
    isolation fence holds here exactly as it does on the request paths. A
    task already `running` is left alone — a slow run must not be doubled
    by the beat that overlaps it.
    """
    now = db.utcnow()
    ran: list[str] = []
    conn = db.connect()
    tenants = conn.execute(
        "SELECT id FROM tenants WHERE deleted_at IS NULL").fetchall()
    for row in tenants:
        tenant = {"id": row["id"]}
        due = conn.execute(
            "SELECT id FROM resident_tasks WHERE tenant_id=?"
            " AND every_hours IS NOT NULL AND next_run_at <= ?"
            " AND status != 'running' ORDER BY next_run_at",
            (tenant["id"], now)).fetchall()
        for d in due:
            try:
                run(tenant, d["id"])
            except ResidentError:
                continue
            ran.append(d["id"])
            audit.record("resident.pulse", tenant_id=tenant["id"],
                         ref=d["id"])
    return {"ran": len(ran), "task_ids": ran}


# --------------------------------------------------------------------------
# the posture, published
# --------------------------------------------------------------------------

def posture(tenant: dict) -> dict:
    """What is running here, for the tenant deciding whether to rely on it."""
    mode = hosting.mode_of(tenant["id"])
    return {
        "resident": True,
        "means": ("the planner, tools, tables, embeddings and inference run "
                  "inside the vault process — no separate orchestration "
                  "service, wherever that process is hosted"),
        "hosting_mode": mode,
        "in_facility": mode in ("colocation", "leased_space", "own_facility"),
        "local_model": local_model(),
        "local_model_standing": model_standing(),
        "standing_tasks": db.connect().execute(
            "SELECT COUNT(*) AS n FROM resident_tasks WHERE tenant_id=?"
            " AND every_hours IS NOT NULL",
            (tenant["id"],)).fetchone()["n"],
        "pulse_seconds": (float(os.environ["PDI_RESIDENT_PULSE"])
                          if os.environ.get("PDI_RESIDENT_PULSE") else None),
        "embedder": (f"local:{os.environ.get('PDI_EMBED_MODEL', 'nomic-embed-text')}"
                     if _ollama_url() else HASHED_EMBEDDER),
        "tools": [{"name": name, "means": t["means"],
                   "leaves_host": t["leaves_host"]}
                  for name, t in sorted(TOOLS.items())],
        "privacy": ("fetched content is sealed in the vault and steps carry "
                    "references; dataset rows are queryable by design and "
                    "written only by this tenant's token; vectors store a "
                    "hash of the text, never the text; every task, step and "
                    "fetch lands on the audit chain"),
    }
