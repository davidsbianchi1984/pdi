import pathlib
"""The README's console gallery, held to the screens on disk.

Every assertion here is about a defect that has already happened in this
repository:

- the README said there were **38** desktop-frame counterparts when there were
  40, and the correction is in the 0.3.3 changelog. Adding screen 41 would have
  made it wrong a second time, in the same sentence;
- a screen can be drawn and never put in the gallery, in which case it exists
  and nobody can see it.

A number written out in prose beside a directory that grows is not a fact, it
is a snapshot — so it is asserted rather than proof-read.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, "README.md")
SCREENS = os.path.join(ROOT, "docs", "screens")


def _readme() -> str:
    with open(README, encoding="utf-8") as fh:
        return fh.read()


def _on_disk() -> set[str]:
    return {f for f in os.listdir(SCREENS) if f.endswith(".svg")}


def test_the_stated_screen_count_is_the_real_one():
    """The sentence that has already been wrong once."""
    src = _readme()
    stated = re.search(r"every one of the (\d+) mobile screens", src)
    assert stated, "the README no longer states a screen count in the expected shape"
    assert int(stated.group(1)) == len(_on_disk()), (
        f"the README says {stated.group(1)} mobile screens; "
        f"{len(_on_disk())} are drawn")


def test_every_referenced_screen_exists():
    """A broken image is invisible to whoever wrote it — it renders as a small
    box on somebody else's machine."""
    referenced = set(re.findall(r"docs/screens/([\w\-.]+\.svg)", _readme()))
    missing = sorted(referenced - _on_disk())
    assert not missing, ("the README points at screens not on disk:\n  "
                         + "\n  ".join(missing))


def test_every_screen_is_shown_somewhere():
    referenced = set(re.findall(r"docs/screens/([\w\-.]+\.svg)", _readme()))
    unshown = sorted(_on_disk() - referenced)
    assert not unshown, ("screens exist that the README never shows:\n  "
                         + "\n  ".join(unshown))


def test_the_gallery_skips_no_number():
    """Adding a screen to a full three-wide row is how a number stops appearing
    while every file still exists and every link still resolves."""
    numbers: list[int] = []
    for name in re.findall(r"docs/screens/([\w\-.]+\.svg)", _readme()):
        head = name.split("-", 1)[0]
        if head.isdigit() and int(head) not in numbers:
            numbers.append(int(head))
    expected = list(range(1, max(numbers) + 1))
    assert sorted(numbers) == expected, (
        "the gallery skips: "
        + ", ".join(str(n) for n in expected if n not in numbers))


def test_no_screen_is_named_something_a_url_cannot_carry():
    """A filename becomes a URL in an `<img src>`; a "?" starts a query string
    and the image silently fails to load."""
    bad = sorted(f for f in _on_disk()
                 if not re.fullmatch(r"[0-9a-z][0-9a-z\-.]*\.svg", f))
    assert not bad, ("screen files whose names are unsafe in a URL:\n  "
                     + "\n  ".join(bad))


def test_the_desktop_app_version_matches_the_api():
    """Three releases shipped installers labelled 0.3.3 from 0.4.x tags.

    `app/package.json` carries its own version and no cut ever bumped it — the
    0.4.0 and 0.4.1 releases both attached installers named 0.3.3, built from
    the right tag but stamped with the stale number. The filename and the
    About box are cosmetic; the auto-updater is not, because it compares
    package versions and will tell an installed app there is nothing newer.

    Same disease as the stale test counts: a duplicated number with nothing to
    fail when the other copy moves. The versions must move together now.
    """
    import json
    import re

    root = pathlib.Path(__file__).resolve()
    while not (root / "app" / "package.json").exists():
        root = root.parent
    desktop = json.loads((root / "app" / "package.json").read_text())["version"]
    api_src = (root / "pdi/api.py").read_text()
    api = re.search(r'version="([\d.]+)"', api_src).group(1)
    assert desktop == api, (
        f"app/package.json says {desktop}, pdi/api.py says {api} — the "
        "installer filenames and the auto-updater follow the first, the "
        "release tag follows the second")
