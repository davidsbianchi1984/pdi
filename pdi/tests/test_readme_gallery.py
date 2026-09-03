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
#: The console galleries moved out of the README when it was cut down to a
#: professional front page — the owner's call. The screens are still shown
#: somewhere, which is what this file holds; somewhere is now here.
GALLERY = os.path.join(ROOT, "docs", "gallery.md")
SCREENS = os.path.join(ROOT, "docs", "screens")

#: A screen is a drawing **or** a photograph. Until 2.7.0 every one of them
#: was an SVG somebody drew, and these guards spelled that out — they
#: globbed `*.svg` and would have called a photographed surface a missing
#: one. The console is now photographed rather than illustrated, so the
#: file extension is no longer what makes a screen a screen.
#:
#:     asked     is there an SVG for this surface
#:     mattered  is there a picture of this surface
SCREEN_KINDS = (".svg", ".png")



def _readme() -> str:
    with open(README, encoding="utf-8") as fh:
        return fh.read()


def _pages() -> str:
    """Everywhere a screen may be shown. The gallery page references images
    relative to docs/, so both `docs/screens/x.svg` and `screens/x.svg`
    count as a reference."""
    with open(GALLERY, encoding="utf-8") as fh:
        return _readme() + fh.read()


#: A slice of a screen, not a screen. Screens taller than the glass are
#: also saved a phone height at a time (`shoot_page` in the camera), and
#: those parts are shown in the gallery's own section — counting them as
#: screens would make the stated count wrong by however many slices the
#: longest screens happen to need.
_A_PART = re.compile(r"-part\d+\.[a-z]+$")


def _on_disk() -> set[str]:
    """Everything in the folder — screens and the parts of long ones.

    The reference checks below want this whole set: a part the gallery
    points at has to exist like any other picture. Only the *count* asks
    a narrower question, and asks it through `_screens_on_disk`.
    """
    return {f for f in os.listdir(SCREENS) if f.endswith(SCREEN_KINDS)}


def _screens_on_disk() -> set[str]:
    """The screens, without the slices of the long ones."""
    return {f for f in _on_disk() if not _A_PART.search(f)}


def test_the_stated_screen_count_is_the_real_one():
    """The sentence that has already been wrong once."""
    src = _pages()
    stated = re.search(r"every one of the (\d+) mobile screens", src)
    assert stated, "the README no longer states a screen count in the expected shape"
    assert int(stated.group(1)) == len(_screens_on_disk()), (
        f"the README says {stated.group(1)} mobile screens; "
        f"{len(_screens_on_disk())} are drawn")


def test_every_referenced_screen_exists():
    """A broken image is invisible to whoever wrote it — it renders as a small
    box on somebody else's machine."""
    referenced = set(re.findall(r"(?:docs/)?screens/([\w\-.]+\.(?:svg|png))", _pages()))
    missing = sorted(referenced - _on_disk())
    assert not missing, ("the README points at screens not on disk:\n  "
                         + "\n  ".join(missing))


def test_every_screen_is_shown_somewhere():
    referenced = set(re.findall(r"(?:docs/)?screens/([\w\-.]+\.(?:svg|png))", _pages()))
    unshown = sorted(_on_disk() - referenced)
    assert not unshown, ("screens exist that the README never shows:\n  "
                         + "\n  ".join(unshown))


def test_the_gallery_skips_no_number():
    """Adding a screen to a full three-wide row is how a number stops appearing
    while every file still exists and every link still resolves."""
    numbers: list[int] = []
    for name in re.findall(r"(?:docs/)?screens/([\w\-.]+\.(?:svg|png))", _pages()):
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
                 if not re.fullmatch(
                     r"[0-9a-z][0-9a-z\-.]*\.(?:svg|png)", f))
    assert not bad, ("screen files whose names are unsafe in a URL:\n  "
                     + "\n  ".join(bad))


# -- the README's own arithmetic -----------------------------------------------

def test_every_test_count_the_readme_claims_is_true():
    """The README says "`module.py`, N tests" in several places, and this
    repository is the third to learn that such a number rots.

    Ported from QRME and JIM-mini, where the same guard found five stale
    claims between them. It is on `guard_divergences.txt` as a question this
    product was not asking, and asking it here found one: `pdi/hosting.py`
    claimed 16 while `test_hosting.py` and `test_hosting_modes.py` held 25.

        asked     does the README's prose read plausibly
        mattered  is each number in it still the number

    A number in prose is a duplicate of something the repository already
    knows, and duplicates drift the moment somebody adds a test — nothing
    fails when a file grows a function, so nothing did.

    The counting is deliberately the dumb kind, as in both siblings: `def
    test_` at column zero, in every file named after the module. One claim
    here names two modules at once (`tutorial.py` and `assistant.py` deliver
    one walkthrough between them), so the files for every module a claim
    names are counted as one bucket — the claim is a single number and has
    to be checked against a single number. This is what moved
    `test_console_guide.py` to `test_tutorial.py`: a test file the
    convention cannot find is a claim nothing checks.
    """
    # The claims lived in the README's capability sections until the front
    # page was cut down; the defect this guards is a *wrong* number wherever
    # one is printed, so the scan covers the README and every markdown page
    # under docs/, and an absence of claims is a legal state.
    readme = _readme()
    for page in sorted(pathlib.Path(ROOT, "docs").glob("*.md")):
        readme += page.read_text(encoding="utf-8")
    claims = re.findall(
        r"`(pdi/[\w/]+\.py)`((?:\s+and\s+`pdi/[\w/]+\.py`)*)[^\n]{0,40}?"
        r"(\d+) tests", readme)
    root = pathlib.Path(ROOT)
    for first, rest, claimed in claims:
        modules = [first] + re.findall(r"`(pdi/[\w/]+\.py)`", rest)
        files = sorted({f for m in modules
                        for f in root.rglob(f"test_{pathlib.Path(m).stem}*.py")})
        assert files, (
            f"README cites {', '.join(modules)} but no test file is named "
            "after any of them")
        actual = sum(len(re.findall(r"^def test_", f.read_text(encoding="utf-8"),
                                    re.M))
                     for f in files)
        assert actual == int(claimed), (
            f"README says {', '.join(modules)} has {claimed} tests; "
            f"{', '.join(f.name for f in files)} hold {actual}")


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
    api_src = (root / "pdi/api.py").read_text()
    lock = json.loads((root / "app" / "package-lock.json").read_text())
    # Five of the twelve places the releasing checklist names — the backend
    # and the console. The other seven are the shells and the README, and
    # they have their own guard in
    # test_the_files_the_release_never_touched.py. Each of these five has
    # drifted at least once (pyproject sat at 0.4.0 through the 0.4.1 cut,
    # the lockfile roots at 0.3.3 through two). Check all five against each
    # other, not one pair.
    versions = {
        "pdi/api.py": re.search(r'version="([\d.]+)"', api_src).group(1),
        "app/package.json":
            json.loads((root / "app" / "package.json").read_text())["version"],
        "app/package-lock.json (root)": lock["version"],
        "app/package-lock.json (packages.'')":
            lock["packages"][""]["version"],
        "pyproject.toml": re.search(
            r'^version = "([\d.]+)"',
            (root / "pyproject.toml").read_text(), re.M).group(1),
    }
    assert len(set(versions.values())) == 1, (
        f"version strings disagree: {versions} — the installer filenames and "
        "the auto-updater follow app/package.json, the release tag follows "
        "pdi/api.py, and pip follows pyproject.toml")
