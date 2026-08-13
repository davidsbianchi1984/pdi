"""Terms of Service: served versioned, receipt recorded at provisioning."""

from pdi import db, terms


def test_terms_served_versioned_with_key_points(client):
    r = client.get("/terms")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == terms.TERMS_VERSION
    assert body["document"] == "docs/terms.md"
    joined = " ".join(body["key_points"]).lower()
    assert "business associate agreement" in joined
    assert "as-is" in joined


def test_tenant_provisioning_records_terms_receipt(client):
    r = client.post("/tenants", json={"name": "acme-health"})
    assert r.status_code == 201
    tenant_id = r.json()["id"]
    row = db.connect().execute(
        "SELECT terms_version, terms_accepted_at FROM tenants WHERE id=?",
        (tenant_id,)).fetchone()
    assert row["terms_version"] == terms.TERMS_VERSION
    assert row["terms_accepted_at"]


def test_custody_is_never_described_as_ownership():
    """A product decides who *holds* a record. It does not get to decide away
    somebody's statutory rights over their own personal data.

    Ported from QRME and JIM-mini, where it guards the storage posture. It
    stood on `guard_divergences.txt` as a question the vault itself was not
    asking — which is the wrong way round: PDI is the product whose whole
    job is holding data about people who are not its customer.

        asked     does the product name an owner
        mattered  does it say that holding is not owning

    Asking it here found the gap. The terms said the Customer owns its data
    and the hosting page said who is awake at 3am; nothing anywhere said
    that PDI's holding confers nothing, or that the data subject's rights
    survive both. Both sentences are now in the words a tenant is shown.

    Checked against the **values a tenant is shown**, not the module source
    — the JIM-mini version of this test first swept the source and failed on
    the comment explaining why ownership is the wrong word, which is the
    fourth time a substring guard in these repositories has tripped on its
    own explanation.
    """
    from pdi import hosting

    shown = " ".join([
        *terms.KEY_POINTS,
        hosting.GUIDANCE,
        *hosting.GUARANTEES,
        *(str(v) for spec in hosting.MODES.values() for v in spec.values()),
    ]).lower()
    for phrase in ("we own your", "the platform owns", "you do not own",
                   "owns your data", "our property"):
        assert phrase not in shown, (
            f"{phrase!r} is an ownership claim, not a custody one")
    assert "custody and never in ownership" in shown, (
        "nothing a tenant is shown says that PDI holding the data is not "
        "PDI owning it")
    assert "statutory rights" in shown, (
        "nothing a tenant is shown says the rights of the people the "
        "records are about survive the arrangement")


def test_the_terms_document_and_the_served_version_agree():
    """The clause above lives in two places — `KEY_POINTS`, which the console
    renders, and `docs/terms.md`, which is the instrument. A version served
    from one while the other has moved is the estate's oldest defect shape:
    a duplicated fact with nothing to fail when one copy changes.
    """
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2]
    doc = (root / terms.DOCUMENT).read_text(encoding="utf-8")
    stated = re.search(r"\*Version ([\d.]+) —", doc)
    assert stated, f"{terms.DOCUMENT} no longer states its version"
    assert stated.group(1) == terms.TERMS_VERSION, (
        f"{terms.DOCUMENT} is version {stated.group(1)} and the API serves "
        f"{terms.TERMS_VERSION}")
    assert "custody" in doc.lower() and "statutory rights" in doc.lower(), (
        "the served key point has no clause behind it in the document")
