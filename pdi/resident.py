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
    with urllib.request.urlopen(req, timeout=60) as resp:  # localhost only
        body = json.loads(resp.read().decode("utf-8"))
    return {"model": f"local:{local_model()}", "text": body.get("response", "")}


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


def _tool_fetch(tenant: dict, args: dict, ctx: dict) -> dict:
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ResidentError("fetch.url needs an http(s) url")
    text = _fetch_text(url)
    key = f"resident/{ctx['task_id']}/{ctx['position']:02d}-fetch"
    vault.put(tenant, key, json.dumps({"url": url, "text": text,
                                       "fetched_at": db.utcnow()}))
    ctx["last_text"], ctx["last_source"] = text, url
    audit.record("resident.fetch", tenant_id=tenant["id"], ref=url)
    return {"result_ref": key,
            "summary": f"fetched {len(text)} chars, sealed at {key}"}


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
    if url and any(w in low for w in ("fetch", "get", "read", "pull",
                                      "download")):
        return {"title": fragment, "tool": "fetch.url",
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


def plan(tenant: dict, goal: str, steps: list[dict] | None = None) -> dict:
    """A task planned and stored, not yet run — running is its own decision.

    Caller-supplied steps are validated against the registry exactly like
    derived ones: the registry is the boundary either way.
    """
    goal = (goal or "").strip()
    if not goal:
        raise ResidentError("a task needs a goal in words")
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
    conn.execute(
        "INSERT INTO resident_tasks (id, tenant_id, goal, planned_by,"
        " status, created_at) VALUES (?,?,?,?,?,?)",
        (task_id, tenant["id"], goal,
         "caller" if steps is not None else "rules-v1",
         "planned", db.utcnow()))
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
    if current["status"] not in ("planned", "failed"):
        raise ResidentStateError(
            i18n.fill(i18n.RESIDENT_TASK_STATE, status=current["status"]))
    conn = db.connect()
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
    conn.execute(
        "UPDATE resident_tasks SET status=?, finished_at=?"
        " WHERE id=? AND tenant_id=?",
        ("failed" if failed else "done", db.utcnow(), task_id, tenant["id"]))
    conn.commit()
    audit.record("resident.task", tenant_id=tenant["id"], ref=task_id)
    return task(tenant, task_id)


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
