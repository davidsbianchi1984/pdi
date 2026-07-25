"""The container image's contract with the code that runs inside it.

These are static checks on the Dockerfile, not a build — CI has no Docker
daemon. They exist because the ways this image can be wrong are quiet ones:
the console silently not served, or — the one that matters here — key
material or a vault database ending up somewhere it must never be. A layer in
a pushed image is not a place to discover either.
"""

import re
from pathlib import Path

from pdi import mobile

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = (ROOT / "Dockerfile").read_text()
DOCKERIGNORE = (ROOT / ".dockerignore").read_text()


def _env(name: str) -> str | None:
    """The value the Dockerfile's ENV instructions give ``name``."""
    m = re.search(rf"^\s*{name}=(\S+)", DOCKERFILE, re.MULTILINE)
    return m.group(1) if m else None


def test_console_dir_points_at_where_the_build_is_copied():
    """The regression this file was written for.

    ``console_dir`` resolves ``app/dist`` relative to the *package*, and after
    ``pip install`` the package lives in site-packages — nowhere near the dist
    the image copies to /srv. Only the explicit override makes the two agree,
    so the image must set it, and to exactly the COPY destination.
    """
    assert _env("PDI_CONSOLE_DIR") == "/srv/app/dist"
    assert re.search(r"COPY --from=console /src/app/dist \./app/dist", DOCKERFILE)
    assert "WORKDIR /srv" in DOCKERFILE


def test_console_dir_honours_the_override(tmp_path, monkeypatch):
    """And that the override is load-bearing in the code, not just the image."""
    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setenv("PDI_CONSOLE_DIR", str(dist))
    assert mobile.console_dir() is None          # nothing built there yet
    (dist / "index.html").write_text("<!doctype html>")
    assert mobile.console_dir() == dist


def test_no_key_material_is_baked_into_the_image():
    """The master key is supplied at runtime and never at build time. An ENV
    or ARG holding it would put the vault's key in a layer of an image that
    is meant to be safe to push to a registry."""
    assert _env("PDI_MASTER_KEY") is None
    assert _env("PDI_ADMIN_TOKEN") is None
    assert not re.search(r"^\s*ARG\s+PDI_(MASTER_KEY|ADMIN_TOKEN)",
                         DOCKERFILE, re.MULTILINE)


def test_no_vault_database_can_ride_along_in_the_build_context():
    """A stray pdi.db copied into an image is somebody's sealed records — and
    the -wal beside it holds writes the main file has not absorbed yet, so
    excluding only *.db would still leak them."""
    ignored = {line.strip() for line in DOCKERIGNORE.splitlines()}
    assert "*.db" in ignored
    assert "*.db-*" in ignored


def test_the_vault_lives_on_a_mounted_volume():
    """Sealed records that outlive their database are unrecoverable, and the
    audit chain proving who read what lives in the same file."""
    assert _env("PDI_DB") == "/data/pdi.db"
    assert 'VOLUME ["/data"]' in DOCKERFILE


def test_service_does_not_run_as_root():
    assert re.search(r"^USER pdi", DOCKERFILE, re.MULTILINE)
    assert DOCKERFILE.index("USER pdi") < DOCKERFILE.index("CMD [")


def test_listens_on_all_interfaces_and_honours_platform_port():
    """Binding to localhost inside a container publishes nothing; and hosts
    that assign a port need it honoured or the health check never passes."""
    cmd = DOCKERFILE[DOCKERFILE.index("CMD ["):]
    assert "--host 0.0.0.0" in cmd
    assert "${PORT:-8100}" in cmd


def test_healthcheck_matches_the_port_the_suite_harness_expects():
    """The suite compose file health-checks pdi on 8100; a default that
    disagreed would leave the service permanently unhealthy there."""
    assert "EXPOSE 8100" in DOCKERFILE
    assert "http://127.0.0.1:8100/health" in DOCKERFILE
