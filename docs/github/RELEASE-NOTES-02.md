# pdi — release notes

Every release published to <https://github.com/davidsbianchi1984/pdi/releases>, newest first. GitHub keeps these in its own database, not in the repository; this page is the copy that travels with a clone.

**255 releases.**

This is one part of a page GitHub is too long to render whole — see [RELEASE-NOTES.md](RELEASE-NOTES.md) for the rest.

**app-v0.54.0 to app-v0.1.1.**

## app-v0.54.0 — PDI app-v0.54.0

- Published: 2026-08-07
- Commit: `5f85a15e6834b7f16974df3f3c98ed62a1d7d7b7`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.54.0>

> ### Cut together at one version
>
> The three products are cut at one version, so this release exists here to keep
> that true. **No code changes in this repo this round.**
>
> The round's work is QRME's, and it is about a number that had been read as
> waste. A shell holding a row it never asks for looks like a translation to
> delete; 263 of QRME's ~335 such rows are asked for by a **sibling** shell, and
> are therefore a to-do list about screens — each one asking why one shell says
> less than the others about the same thing.
>
> Two were closed. The iPhone had **no camera-permission state at all**, so a
> person who declined got a black screen and never saw *"Nothing is recorded —
> frames are read and discarded"* — a privacy promise only Android readers had
> been given. And Windows was printing "scan(s)" and "picked up" as English
> literals with those exact strings translated beside them.
>
> This repo's version of the same argument: a refusal or a promise is only
> kept if every reader gets it. A vault that states its posture in one language
> has stated it to some of its auditors. The guard QRME built extracts every
> literal from every screen and compares it against that shell's own table —
> and its first version could not see the bug it was written for, which the
> injection pass caught before it shipped.
>
> Cut together with QRME and JIM-mini at **app-v0.54.0**.

## app-v0.53.1 — PDI app-v0.53.1

- Published: 2026-08-07
- Commit: `89b33463dbe5cc9706dc08193151e6139ae89a9b`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.53.1>

> ### `operator_can_decrypt: false`, checked against the whole database
>
> `custody()` reports that a tenant under **held** custody has a key "the
> deployment never stores". That sentence is why outsourced hosting of this
> vault is a different product from every other one, and it is the sentence a
> security review quotes.
>
> What checked it was a literal read back out of the dict that hardcodes it —
> `assert body["operator_can_decrypt"] is False` — and one real but narrow test
> reading **two columns of one table**: `SELECT check_value, config FROM
> tenant_keys`. That is where a first implementation would put a key, so it was
> the right place to look first. It is not the claim. The claim is *nowhere*.
>
> A key does not have to be stored on purpose to be stored. It rides a header on
> every request, and this deployment has an operations journal, an audit trail,
> an error path and a retention sweep — any of which could carry a request
> detail into a row without anybody deciding to.
>
> So the sweep walks **every table and every column**, from `sqlite_master`
> rather than a hand-written list, looking for the key in every representation
> it could wear: the base64 the client sends, the raw bytes, and hex. Then it
> does it again while using the key on every door, and again after a *refused*
> key, because the error path is where secrets go to be logged. The record's
> plaintext gets the same treatment, under both custody modes — "the operator
> cannot open these records" and "the plaintext is not sitting in a column
> somewhere else" are different claims and only the first had a test.
>
> **Nothing leaked.** Seven assertions, including one that writes the key into a
> column on purpose and requires the sweep to name the table — a guard nobody
> has watched fail is a guard nobody should trust.
>
> Cut together with QRME and JIM-mini at **app-v0.53.1**.

## app-v0.53.0 — PDI app-v0.53.0

- Published: 2026-08-07
- Commit: `f19bd688d0d16ca7a19f1727c6b9f75c31657d6b`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.53.0>

> ### Cut together at one version
>
> The three products are cut at one version, so this release exists here to keep
> that true. **No code changes in this repo this round.**
>
> The round's work is JIM-mini checking whether its posture blocks were kept
> rather than merely stated. They were — but nothing had been testing it, and one
> sentence claimed more than the code delivered.
>
> This is the vault's own subject. A posture block is this repo's central idea
> exported to a bridge: state what can and cannot be done, in a field a client
> renders, rather than in a comment. What this round adds to that idea is the
> second half — **a stated posture needs a test that could catch it lying**, and
> the test cannot be a read of the statement. It has to take the action and look
> at what moved.
>
> And the correction is the one an auditor makes: a list of refusals that never
> names what *is* kept invites a reader to conclude nothing is. The answer now
> names the record it writes.
>
> Cut together with QRME and JIM-mini at **app-v0.53.0**.

## app-v0.52.0 — PDI app-v0.52.0

- Published: 2026-08-07
- Commit: `2ecc2d52b688fd4bdbe319cf3ad460805e78682a`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.52.0>

> ### Cut together at one version
>
> The three products are cut at one version, so this release exists here to keep
> that true. **No code changes in this repo this round.**
>
> The round's work is JIM-mini's presence learning what a room may hear. On a
> surface other people can hear, a vital, a condition, a medication, money, a
> journal or a crisis is held back and shown on a screen instead.
>
> Two things there are this repo's kind of decision. **The withholding happens
> before the content exists** — the decision is made server-side ahead of any
> synthesis, rather than handed to a client with a flag attached, which is the
> same reason this vault decrypts nothing it has not first decided the caller may
> read. And **the refusal is legible**: the answer names the categories it held
> and why, the way this repo's posture blocks state what an operator can and
> cannot decrypt. A guardian that goes quiet without saying why has taken the
> beat away rather than moved it, and a vault that refuses without saying what it
> refused is one nobody can audit.
>
> Cut together with QRME and JIM-mini at **app-v0.52.0**.

## app-v0.51.0 — PDI app-v0.51.0

- Published: 2026-08-07
- Commit: `9975984f09b929445bcbc50516b15026edccfa9c`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.51.0>

> ### Cut together at one version
>
> The three products are cut at one version, so this release exists here to keep
> that true. **No code changes in this repo this round.**
>
> The round's work is a dial and a count. JIM-mini's presence gains a
> **bearing** — companion by default, professional on request — and QRME's
> profiles start stating **how many people they are talking to**.
>
> Both are this repo's kind of decision. The bearing is a **register and never a
> capability**: it changes wording and changes nothing about what the guardian
> watches or which safety paths run, and that claim ships as a field a client
> renders rather than a line in a docstring — the same reason this repo's
> posture blocks state what an operator can and cannot decrypt in the response
> rather than in a comment. And the count is **offered rather than asked for**,
> which is the vault's own argument about disclosure: a fact somebody has to
> earn access to in order to learn is a fact the system was withholding, and the
> withholding is what turns an ordinary property into a betrayal.
>
> Cut together with QRME and JIM-mini at **app-v0.51.0**.

## app-v0.50.0 — PDI app-v0.50.0

- Published: 2026-08-06
- Commit: `dbd7d1debbb5c14d8a88eb2593c94d1983decd89`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.50.0>

> ## Cut together at one version
>
> No code changes in this repo this round. The work is JIM-mini's presence: a coach that speaks first, deciding what to say from six areas of somebody's own history with no network and no model, and letting a model only reword the result.
>
> Two decisions there are this repo's kind of decision. **The refusals are on the wire** — what the presence will not be is a field a client renders, not a line in a docstring, the same reason this repo's posture blocks state what an operator can and cannot decrypt in the response rather than in a comment. And **the offline path is the floor rather than the fallback**: the useful version of "works without the network" is the one where the network adds wording and never capability, which is what a vault has to be too.
>
> Cut together with QRME and JIM-mini at app-v0.50.0.

## app-v0.49.0 — PDI app-v0.49.0

- Published: 2026-08-06
- Commit: `1a8018cc8a42ac7a8b99ef50f1c53e83c8838257`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.49.0>

> ## Cut together at one version
>
> No code changes in this repo this round. The work is QRME's public stream — recorded video, live rooms and staffed desks in one swipeable surface — and JIM-mini's GET-only door onto it.
>
> Two decisions there are this repo's kind of decision. The rule about what plays without being asked for is asserted **on the wire** rather than in each of four clients, the same shape as this repo's posture blocks, which state what the operator can and cannot decrypt in the response rather than in a comment a client may not read. And JIM passes QRME's flag through whole rather than recomputing it: two implementations of one promise is one implementation and one bug waiting for the day the first changes its mind.
>
> Cut together with QRME and JIM-mini at app-v0.49.0.

## app-v0.48.3 — PDI app-v0.48.3

- Published: 2026-08-06
- Commit: `22a3b70fbebd4e021fb7a798c7d2a31e671f9126`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.48.3>

> ### Custody and Continuity read in the tenant's language
>
> The next bite out of this console's English, and not the largest screens first:
> **Custody** and **Continuity** are decisions rather than descriptions, which is
> the criterion this audit has used since the alarm surface.
>
>     229 → 177
>
> **Custody** answers the only question this product exists for — *can the
> operator decrypt this?* — and carries the sentence naming the honest measure of
> bring-your-own-key: how much of the vault the operator could not touch even
> when asked to. It also says, in ten languages now, that the audit trail
> survives a deletion: *a vault that could erase the record of erasing something
> would not be evidence of anything*.
>
> **Continuity** is what happens to a sealed file after a death. A bequest is a
> standing instruction that grants nothing when written. Its activation needs a
> different credential from the one that wrote it, *because the person who wrote
> the bequest cannot also be the one who declares its condition met*. And the
> heir holds two separate secrets of which neither works alone.
>
> ### The record predicted this, and was right within one round
>
> `console_native_split.txt` said at 0.48.2 that it *"becomes a real record the
> moment a screen exists on both sides"*. It did. The table went to 133 rows and
> the guard found one disagreement immediately: `co.admin.ph` against Android's
> `nadm.token`, both **Admin token**, differing in Portuguese, Hindi and Arabic.
> The console adopted the shells' wording and the count returned to zero.
>
> That is the argument for building a table with the comparison already running.
> The sibling products reached 102 and 25 disagreements by growing two tables
> past each other for many releases with nothing watching.
>
> ### Four more guards followed their sentences
>
> 0.48.2 recorded that localizing a screen blinds every guard that greps it for
> English. This round hit four: the custody question, the reseal note, the
> difference between revoking a grant and revoking a bequest, and the difference
> between *nothing paged* and *nothing could have been paged*. All four now go
> through `_says()` — the screen must ask for the key **and** the table must hold
> it in all ten languages. Six of the fourteen screen-greps are converted; the
> other eight go blind the round their screen is localized, and are expected to.
>
> ### Changed
>
> - `Custody.tsx` and `Continuity.tsx` read their words from the table — 38 and
>   41 sites, 79 new rows across ten languages.
>
> Cut together with QRME and JIM-mini at app-v0.48.3.

## app-v0.48.2 — PDI app-v0.48.2

- Published: 2026-08-06
- Commit: `7c8ee5f1710513ccaa0481fe808e9fc65d4f47b5`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.48.2>

> ### The console gets a table, and the language picker goes first
>
> 0.48.1 recorded what this repo's console cost: fourteen screens, 250 English
> strings, no `app/src/l10n.ts` at all, and a **language picker** on `Guiding.tsx`
> that changed what the backend said and nothing that the console said.
>
> This round builds the table and wires that screen, for the reason it is the
> sharpest one: **the screen where a person chooses their language is the first
> that has to read in it.** 36 rows, ten languages, and the chosen language now
> rides in the session — so every screen wired after this one is a table entry
> rather than a piece of plumbing.
>
>     250 → 229
>
> ### Two choices in that table, both answers to findings next door
>
> * **No formal/informal split.** 0.48.1 found QRME's console addressing a German
>   reader as *Sie* in 204 rows while its phones said *du* in 60 — one product
>   making two contradictory claims about the relationship. These rows avoid the
>   T–V distinction wherever the language allows it, so the question does not
>   arise and cannot drift.
> * **Portuguese is pt-PT** — *ficheiro*, *ecrã* — matching the shells.
>
> ### The zero that changed meaning
>
> `console_native_split.txt` was an empty floor at 0.48.1 because there was
> nothing to compare. It is still empty, and now for a different reason: 36
> console rows and one English string in common with each shell, because the two
> tables are still about different screens. The record has been rewritten to say
> which zero it is — a record that outlives the code it describes is what
> `test_a_record_that_outlived_the_code.py` exists to stop.
>
> The sibling products reached 102 and 25 disagreements by growing two tables
> past each other without ever comparing them. This one is being grown with the
> comparison already running.
>
> ### Localizing a screen blinded a guard, and the guard was right
>
> Wiring `Guiding.tsx` turned `test_the_guide_screen_keeps_both_of_its_refusals`
> red. That check makes sure the console keeps saying the two things the server
> insists on — that the guide has no face, and that it does no machine
> translation — and it did it by grepping the screen for the English. The
> sentence moved into the table; the screen still says it; the grep went blind.
>
>     asked     is this sentence in the screen file
>     mattered  does the screen say it, in every language it offers
>
> This audit's own shape, arriving inside the audit's guards. The fix follows the
> sentence rather than weakening the check: the screen must ask for the key and
> the table must hold it in **all ten languages**, which is stricter than the
> grep it replaces, since that only ever proved the English existed.
> `test_the_door_and_the_wire.py` greps fourteen screens this way, so each will
> go blind the round its screen is localized — recorded in
> `console_untranslated.txt` so the next round expects it.
>
> ### Added
>
> - `app/src/l10n.ts` — the console's first localization table, with
>   `deviceLanguage()` reading the browser before a tenant has chosen, matching
>   what the shells have done since the accountless-screen round.
> - `pdi/tests/test_the_three_shells_say_the_same_thing.py` and
>   `pdi/tests/native_shell_split.txt` — the third axis, at a floor of zero here.
>
> ### Changed
>
> - `Guiding.tsx` reads all 31 of its own strings from the table.
> - The session carries the tenant's chosen console language.
>
> Cut together with QRME and JIM-mini at app-v0.48.2.

## app-v0.48.1 — PDI app-v0.48.1

- Published: 2026-08-06
- Commit: `bd7c523f298d2618e264048a8be3306fd3eb3511`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.48.1>

> `###` This console has no table, and nothing had ever said so
>
> The shared guard this round compares the desktop console's table with the three
> shells'. QRME found 102 disagreements, JIM-mini 25.
>
> **This repo cannot have that defect, because `app/src/l10n.ts` does not
> exist.** The console is fourteen screens of English — 250 strings — while all
> three native shells carry a ten-language table and the backend answers a tenant
> in the language they chose.
>
> The sharp part is not that it is English. `Guiding.tsx` renders a **language
> picker**, backed by `GET /languages` and `PUT /language`. A tenant opens the
> vault's console, selects Spanish, and the backend begins answering in Spanish
> inside a frame that stays entirely English — under headings reading **Sealed**,
> **Recipient**, **Custody**, **Carriers**, **Positions** and **Continuity**.
>
>     asked     do this product's two tables agree
>     mattered  does this product have two tables
>
> That is the opening finding of this whole arc — the chrome answers in your
> language and nothing behind it does — in the one place where the chrome does
> not answer either. Both sibling products audited their consoles rounds ago and
> drove the number to a floor. This one had no record, no guard, and no count.
>
> ### Added
>
> - `pdi/tests/console_untranslated.txt` — 250 strings, worst screens named,
>   ratcheted in both directions: it may not rise, and a fall of more than sixty
>   is treated as an extractor that stopped matching rather than a round of work.
> - `pdi/tests/console_native_split.txt` — an empty floor that says **no console
>   table** in its own text, and a check that fires if that phrase is ever
>   removed while the table is still absent. A zero meaning *nothing to compare*
>   must never be read as *nothing wrong*.
> - `pdi/tests/test_the_desktop_and_the_phone_say_different_things.py`, holding
>   both.
>
> The screens themselves are a round of their own. This one makes the number
> true, visible and unable to rise.
>
> Cut together with QRME and JIM-mini at app-v0.48.1.

## app-v0.48.0 — PDI app-v0.48.0

- Published: 2026-08-06
- Commit: `cafe810019750a5bdd5a44a72098c8b974f3f421`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.48.0>

> ### The guard arrives before the rows do
>
> The shared guard this round is
> `test_the_same_sentence_translated_twice.py`: per shell, the English strings
> carried by two or more keys whose ten translations disagree. QRME found 54 such
> strings on iOS with 43 already drifted; JIM-mini found six with six drifted.
>
> **This repo has none**, and that is a measurement rather than an achievement.
> These three tables hold 51, 64 and 58 rows because most of this product's
> screens are still English — `native_screens_untranslated.txt` records 65, 59
> and 69 — and a table holding few sentences cannot hold one twice. The record
> here is an empty floor: the *before* picture, with the guard in place so that
> the rows still owed arrive checked rather than audited two releases later,
> which is exactly what happened in the sibling repo.
>
>
> Cut together with QRME and JIM-mini at app-v0.48.0.

## app-v0.47.9 — PDI app-v0.47.9

- Published: 2026-08-06
- Commit: `d730bfcedffe8a7f4940e64c1fbb9bb9f685ab2b`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.9>

> ### Cut together at one version
>
> The three products are cut at one version, so this release exists here to keep
> that true. **No code changes in this repo this round**, beyond the shared guard:
> `_ARRAY` arrives, the Swift twin of the `listOf` shape found in Kotlin at
> 0.47.6 — an array literal handed to a loop, whose strings never start a
> `Text(`. It found nothing on these shells.
>
> The round's work is QRME's, and it is a correction rather than a bite: the
> record that has called 335 rows a deletion backlog for three releases was
> wrong. 263 of them are rows one shell holds and a sibling asks for — the same
> screen saying less on one shell than the others. What that mislabelling was
> hiding is the voiceprint consent block, whose three sentences were hardcoded
> English on the iPhone while both siblings took them from the table.
>
> Cut together with QRME and JIM-mini at app-v0.47.9.

## app-v0.47.8 — PDI app-v0.47.8

- Published: 2026-08-06
- Commit: `066af3e75520c5e6cae1cd1ead071d5cf5688e4f`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.8>

> ### The sentence that says how to get the file back
>
> Transfers is the largest single concentration of English left anywhere in the
> three products — 28 strings on the iPhone, 32 on the desktop, 17 on Android —
> and it is the screen this vault exists for: seal a file for a recipient, or ask
> a counterparty to send one in.
>
> Two of its sentences are a hazard rather than a discourtesy, and they are the
> reason it was worked next:
>
> > Hand this to the recipient out of band; it is the only way to retrieve the file.
>
> > Send this to the counterparty out of band; it is their only way in.
>
> Each sits directly under a token the same screen says is **shown once**. A
> reader who cannot read the sentence does not lose a nicety; they lose the file.
>
> **Fifteen new rows, seventeen carried across from the table that already held
> them, and the screen wired on all three shells** — 50 literals on iOS and
> Android, 34 on the desktop.
>
> ### Three shapes this arc already settled, applied rather than rediscovered
>
> * the **direction picker** keeps its raw values (`Outbound`, `Intake`) as the
>   thing the screen switches on and looks a key up for the label — a localized
>   raw value is a control that quietly stops matching, which is the 0.47.4 rule;
> * the Android strip resolves keys out of its `listOf`, the 0.47.6 idiom;
> * the desktop's labels move out of XAML attributes into a `Localize()` the
>   constructor calls, the 0.47.7 idiom — and the three buttons **inside**
>   `DataTemplate`s take their words from the row, because a template is stamped
>   once per row and `x:Name` addresses only the last one.
>
> ### One row that was dead for an honest reason
>
> `nfil.programs` sat in the desktop's table asked for by nothing, because that
> page had no Programs label at all while the phones both did. Wired rather than
> deleted: the rule this record has carried since 0.47.6 is that a row which
> looks dead is evidence about the screen before it is evidence about the row.
>
> **iOS 90 → 65, Android 73 → 59, Windows 101 → 69.** Dead rows to zero.
>
> Cut together with QRME and JIM-mini at app-v0.47.8.

## app-v0.47.7 — PDI app-v0.47.7

- Published: 2026-08-06
- Commit: `6ce5f93f8bcc97c80afdd17672673acc5b05f63d`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.7>

> ### The console's own posture statement was English
>
> 0.47.6 derived the label rule for Kotlin. This round covers the other two
> syntaxes, and on this shell the Windows half is what mattered: `_XAML` reads
> attributes, and the settled idiom here is `x:Name` plus
> `Foo.Text = L10n.T("key")` in a `Localize()`, so a label nobody localized sits
> in the code-behind as an assignment `Text="` cannot match.
>
>     asked     is this an attribute on an element
>     mattered  does this end up as the words on an element
>
> What it hid is the paragraph this console uses to state what it does about
> failures — *This app can send a count of what failed … Not what you typed, not
> who you are, not which profile.* — and its two-step reveal, *Show what would be
> sent* / *Hide what would be sent*. A promise about privacy that only English
> readers can read is a promise made to some of the people it is about.
>
> Beside it, **Rotated — every record re-sealed under the new version.**, which
> is the sentence an operator reads after rotating the key the whole vault is
> sealed under.
>
> The Swift derivation finds one wrapper here, `stat`, naming the two counters on
> the front screen. It is derived rather than named anyway: the point of the rule
> is that a wrapper added tomorrow is found without anybody remembering to add it.
>
> **10 call sites wired, 8 rows added, 1 copied.** Records unchanged at iOS 90,
> Android 73, Windows 101.
>
> Cut together with QRME and JIM-mini at app-v0.47.7.

## app-v0.47.6 — PDI app-v0.47.6

- Published: 2026-08-06
- Commit: `8a1b12a795a104426d7c691beeb294a0e9a706e7`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.6>

> ### The buttons that write to the vault were English
>
> The untranslated-screens rule arrives here widened, in the round QRME widened it, because these three files are one guard copied twice. Compose has no `Button(text)`: a button on this shell is a `Box` with a `Text` inside it, called by name — `BrandButton("Seal record")`, `SmallAction("Rotate key")`, `labeledField("Admin token", tok, "…")`. The Kotlin pattern list was `Text(` and nothing else, so this record has been ground down for a dozen rounds with every button on the shell in English underneath it.
>
>     asked     does the string start a `Text(`
>     mattered  does the string end up inside one
>
> What that hid here is the write path: *Seal & create*, *Seal record*, *Rotate key*, *Retire old*, *Request file*, *Submit into the newest open intake* — and beside them the field where an operator types an admin token. A person who cannot read the button is a person sealing a record they did not understand.
>
> **37 call sites wired, 33 rows added.** Android 75 to 73.
>
> Cut together with QRME and JIM-mini at app-v0.47.6.

## app-v0.47.5 — PDI app-v0.47.5

- Published: 2026-08-06
- Commit: `d15131f2c3858794a71b0fa5a13bcdef51591c19`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.5>

> ### The welcome screen greeted everyone in English
>
> Welcome is the accountless screen: whoever reads it has no tenant yet, so the
> language cannot come from a stored setting. This repo's own `L10n` docstring
> has said since it was written that an accountless surface must pass
> `DeviceLanguage()`. This screen was never given it — on all three shells — so
> `AppState.Language` answered "en" for every reader on earth.
>
> Now localized on iOS, Android and the desktop, from the device's own setting.
>
> ### The sign-out fix, in the third product
>
> The desktop's **Sign out** sits in `NavigationView.PaneFooter`, and the loop
> that localizes the nav walks `Nav.MenuItems` — which the footer is not one of.
> QRME found this in its own copy of the file at 0.46.9. JIM-mini found it at
> 0.47.2. This is the third product with the same nav, and here the table did
> not even hold `action.sign_out`.
>
> Beside it: the desktop's only **Refresh** button was hardcoded English, next
> to an `action.refresh` row translated into ten languages that nothing asked
> for.
>
> ### The dead-key guard, ported
>
> JIM-mini's guard arrives here too, and its backlog file is empty from day one.
> It found five dead rows — `action.save` on all three shells, `action.refresh`
> on the two phones. Generic verbs added in advance for a Save button no screen
> ever grew. JIM reached exactly this list at 0.40.7; its instruction was "wire
> one or delete one". One was wired, the rest deleted.
>
> One thing did not port cleanly, and that is worth writing down. The guard's
> own liveness check asserts a table has at least twenty rows, a number chosen
> against a table of roughly a thousand. PDI's chrome table is small on purpose
> — this product localizes its explanatory prose server-side by the tenant's
> language, and the table covers only the frame around it. A threshold carried
> across without its premise fails on a table that is exactly the size it should
> be.
>
> **294 → 266.** iOS 94 → 90, Android 78 → 75, Windows 122 → 101. Ten of the
> Windows drop were never English prose: the language picker's items are
> endonyms — each language named in its own language — and they moved out of
> XAML attributes into a table in the code-behind, where they read as data.
>
> Cut together with QRME and JIM-mini at app-v0.47.5.

## app-v0.47.4 — PDI app-v0.47.4

- Published: 2026-08-06
- Commit: `81e93bbc269a481731aca386d543c9adc8ec0d1a`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.4>

> ### Version alignment
>
> No PDI code changed this round. The work was JIM-mini's Overview screen and
> the tab strips on Care, Life and Safety, where the English sat in an enum's
> raw values — 229 → 150 across its three shells.
>
> PDI's own native record stands at 294, and the enum-as-label shape is worth
> looking for here when that record is next worked.
>
> Cut together with QRME and JIM-mini at app-v0.47.4.

## app-v0.47.3 — PDI app-v0.47.3

- Published: 2026-08-06
- Commit: `634102c49d6cda3cd7f4d7fb50510b9bc46835b2`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.3>

> ### The guard-on-guard, ported
>
> `clientpaths.py` is byte-identical in all three repos, so PDI gains the same
> check: every path-shaped literal is either inside a call shape the route audit
> knows, or recorded with the reason it is not a request.
>
> It found nothing new here — this shell's two unattributed literals are the
> console's `/app` prefix test and a regular expression in the iOS problem
> reporter that begins with a slash. Both are recorded with their reason, and
> the record is ratcheted in both directions so it cannot become a place where a
> real blind spot hides.
>
> Finding nothing is the result, not the absence of one: the same check found
> six false doorless entries in JIM-mini and two invisible calls in QRME.
>
> Cut together with QRME and JIM-mini at app-v0.47.3.

## app-v0.47.2 — PDI app-v0.47.2

- Published: 2026-08-06
- Commit: `758d819b492928ca35260a724fafb226ad2173d6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.2>

> ### Version alignment
>
> No PDI code changed this round. The work was in JIM-mini: the sign-out control
> QRME fixed two releases ago and nobody carried across, then the Family and
> Connect screens on all three of its native shells.
>
> The habit that found it applies here too — this repo's guards are the
> sibling's guards, copied, so a fix in one of them is owed to all three. PDI's
> native record stands at 294.
>
> Cut together with QRME and JIM-mini at app-v0.47.2.

## app-v0.47.1 — PDI app-v0.47.1

- Published: 2026-08-06
- Commit: `82d3835b02ea1e8a3525930b6a4cb149012be48b`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.1>

> ### The ternary blind spot, ported and corrected
>
> This repo's native-shell guard is the sibling's guard, copied, so it carried
> the same blind spot: a string chosen by `cond ? "A" : "B"` is not at the
> start of an argument list, and every pattern looked only there. The widening
> is ported verbatim from the repo that found it, with the two tests that hold
> it — one fails if the rule stops matching, one fails if it starts counting
> lone tokens.
>
> The recorded counts rise by **12**: iOS 88 → 94, Android 75 → 78, Windows
> 119 → 122. Nothing regressed. Twelve strings were always there and could not
> be seen.
>
> Cut together with QRME and JIM-mini at app-v0.47.1.

## app-v0.47.0 — PDI app-v0.47.0

- Published: 2026-08-06
- Commit: `4d63380c9f1f8f8a668c44c30635e90fa82be80e`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.47.0>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed. QRME found that its native-shell
> measurement could not see a string chosen by a ternary — `cond ? "Verifies" :
> "Does not verify"` was invisible on every shell — corrected the count from 68
> to 125, and then ran it to 7, none of which contains English.

## app-v0.46.9 — PDI app-v0.46.9

- Published: 2026-08-06
- Commit: `3d780f9a010c3e43d28e15f8eae9cc9f3fda2de5`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.9>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed. QRME localized the six screens that exist
> on all three of its shells — 212 English strings behind the tab bars down to
> 68 — and fixed a sign-out button on Windows that read "Sign out" in every
> language because it sat outside the loop that localizes the navigation.

## app-v0.46.8 — PDI app-v0.46.8

- Published: 2026-08-06
- Commit: `8593f60303a9d382b218255634eddeac1054b42e`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.8>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed. QRME finished the console that runs a
> profile's public reach on all three shells — 368 English strings behind the
> tab bars down to 212 — and replaced a US-only crisis number, shown in ten
> languages, with the local-services wording this product settled on first.

## app-v0.46.7 — PDI app-v0.46.7

- Published: 2026-08-06
- Commit: `6da615bf955e2e4f2633e9039dfec521c646db4a`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.7>

> ## Version alignment
>
> The three products are cut together, so one number names one combination of all three. No PDI code changed, and nothing new crosses into the vault.
>
> QRME localized Signatures and Voice on all three shells — **470 → 368** — and closed a gap where two cards had been done on two shells and missed on the third, at the cost of no new rows at all.

## app-v0.46.6 — PDI app-v0.46.6

- Published: 2026-08-05
- Commit: `3337d587382c3b33a9a40507fd829d2170f19955`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.6>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed. QRME finished its settings screen and did
> Community on all three shells — 590 English strings behind the tab bars down
> to 470 — and fixed a relationship picker that had been rendering the API's
> enum members as if they were words.

## app-v0.46.5 — PDI app-v0.46.5

- Published: 2026-08-05
- Commit: `f017c95a84a452a8239128e222f568d7c80ba1ca`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.5>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed. QRME's round was its phones: the first
> screen and the settings screen localized on iOS, Android and Windows — 703
> English strings behind the tab bars down to 590 — and its Android shell,
> which turned out not to compile, fixed and guarded.

## app-v0.46.4 — PDI app-v0.46.4

- Published: 2026-08-05
- Commit: `f36d4a017219d7c701900dd9ebc4c9f0b317b5a3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.4>

> ### Forty fields a person fills in, and nothing on the form said what they were
>
> The field-label record explains why an unmapped field keeps its API name:
> inventing a word for a field nobody labels is worse than an identifier the
> reader can match to the form. True, and it had become a reason not to look
> at the forms.
>
> Forty of the 91 rows had a control a person operates:
>
> - **five bare `<select>`s** with no label at all — the connector direction,
>   the robot model, the beacon's kind, what a scan discloses, the language
>   picker
> - **eight boxes carrying only a placeholder**, which is an example rather
>   than a name: filename, recipient, platform, source, reference, label,
>   question, the note to translate
> - **a date input** with neither, next to two that at least said theirs in
>   grey until somebody typed over them
> - **the whole Positions questionnaire** — nineteen labelled fields, from
>   *Oversight level* to *Interested in reskilling / repositioning*
>
> The labels went onto the forms first and were then ported into the table, in
> that order. The record's rule is that the sentence agrees with the form, and
> a form that says nothing leaves nothing to agree with.
>
> Fourteen of the rows are ported verbatim from QRME rather than written
> again — `kind`, `label`, `language`, `model`, `direction`, `platform`,
> `source`, `ref`, `question`, `text`, `tone`, `industry`, `scope`, `role` —
> which the cross-product check in the suite enforces. It earned its keep this
> round: a first draft had *Clase* where QRME says *Tipo*.
>
> **91 → 51.** What is left is what the record always claimed it was: groups,
> ids a client fills in from the row it is looking at, enum members and flags.
>
> Cut together with QRME and JIM-mini at app-v0.46.4.

## app-v0.46.3 — PDI app-v0.46.3

- Published: 2026-08-05
- Commit: `67540f848d545e473d66450be9e88dc6474b2b91`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.3>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console-untranslated record reached its floor
> this round: 25 → 1.

## app-v0.46.2 — PDI app-v0.46.2

- Published: 2026-08-05
- Commit: `001f632c232a7baa5aef7306217de39e1058d7c7`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.2>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 69 → 25.

## app-v0.46.1 — PDI app-v0.46.1

- Published: 2026-08-05
- Commit: `b6aa75fd5ffdd9d4247c8701da13151923ad6d3d`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.1>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 116 → 69.

## app-v0.46.0 — PDI app-v0.46.0

- Published: 2026-08-05
- Commit: `aa3483a7e77413618e4af2d3135c07e1d9873a13`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.46.0>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 180 → 116.

## app-v0.45.9 — PDI app-v0.45.9

- Published: 2026-08-05
- Commit: `8583051f97f02be5c214fb20c003367022de0e5d`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.9>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 254 → 180.

## app-v0.45.8 — PDI app-v0.45.8

- Published: 2026-08-05
- Commit: `cbce846b2aa64f17c924905964566b01b3126b94`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.8>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 338 → 254.

## app-v0.45.7 — PDI app-v0.45.7

- Published: 2026-08-05
- Commit: `b632b446631ced93a6264d6c1fd2a8879341cf97`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.7>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed, and nothing new crosses
> into the vault. QRME's console record: 425 → 338.

## app-v0.45.6 — PDI app-v0.45.6

- Published: 2026-08-05
- Commit: `d5dfcd2c1633662ecdc9977c9374c643faebc027`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.6>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> lobby, presence and voice screens, 516 → 425. Nothing new crosses into
> the vault.

## app-v0.45.5 — PDI app-v0.45.5

- Published: 2026-08-05
- Commit: `f5656418c7d6243517a9bbb8c7ccac1d4fc829ca`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.5>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> objection, live-presence and marketplace screens, 616 → 516. Nothing
> new crosses into the vault.

## app-v0.45.4 — PDI app-v0.45.4

- Published: 2026-08-05
- Commit: `99a71a804f9a15bd39cb81962346e5c315246da1`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.4>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> watch-party, delegation and beacon screens, 724 → 616. Nothing new
> crosses into the vault.

## app-v0.45.3 — PDI app-v0.45.3

- Published: 2026-08-05
- Commit: `570200573118a8ca0056ae47bafcf37e1f3220fc`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.3>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> succession, signing and placement screens, 848 → 724. Nothing new
> crosses into the vault.

## app-v0.45.2 — PDI app-v0.45.2

- Published: 2026-08-05
- Commit: `6e206139c156c83ab7d6dc54b934a0ee78d230d3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.2>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized
> Exchanges, Reaching and Visiting, taking its console-untranslated
> record from 978 to 848. Nothing new crosses into the vault.

## app-v0.45.1 — PDI app-v0.45.1

- Published: 2026-08-05
- Commit: `853d1c516903cdb25faf5590e4e3f9b4eb3d3bce`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.1>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — JIM ran its
> console-untranslated record to zero. Nothing new crosses into the
> vault.

## app-v0.45.0 — PDI app-v0.45.0

- Published: 2026-08-05
- Commit: `958a895a98bffb52d6e9bbbd70dcdd8e1c030d0b`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.45.0>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Workshop and Bodies screens, taking its console-untranslated record
> under a thousand, and JIM localized three more. Nothing new crosses
> into the vault.

## app-v0.44.9 — PDI app-v0.44.9

- Published: 2026-08-05
- Commit: `747c653a3c6ece4f9a2a94c3bd71676e1f9982aa`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.9>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Identity screen and JIM its Medications and Wellness screens. Nothing
> new crosses into the vault.

## app-v0.44.8 — PDI app-v0.44.8

- Published: 2026-08-05
- Commit: `e4b587139bfef4cd40d4450142faa44341ae68cc`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.8>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Remainder screen and JIM its Settings screen. Nothing new crosses
> into the vault.

## app-v0.44.7 — PDI app-v0.44.7

- Published: 2026-08-05
- Commit: `2c7846e86949ae2937a813b8d7adbcb5ff757b75`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.7>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Referrals screen and JIM its Bearing screen. Nothing new crosses
> into the vault.

## app-v0.44.6 — PDI app-v0.44.6

- Published: 2026-08-05
- Commit: `c81a8a9e4261578c976ac5203daa39ee8e9f38cb`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.6>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Desk screen and JIM its Reach screen. Nothing new crosses into
> the vault.

## app-v0.44.5 — PDI app-v0.44.5

- Published: 2026-08-05
- Commit: `544f83b6c55d1304f66b7ca44e30f2f503b9ba88`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.5>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Selling screen and JIM its Baseline screen. Nothing new crosses
> into the vault.

## app-v0.44.4 — PDI app-v0.44.4

- Published: 2026-08-05
- Commit: `693ee4c1c8511d2cf2b3759a79f055ded2ba5ef1`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.4>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Control Center and JIM its Attending screen. Nothing new crosses
> into the vault.

## app-v0.44.3 — PDI app-v0.44.3

- Published: 2026-08-05
- Commit: `fba0420de3b464f3a6c3f7d787ed7a054b2ff536`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.3>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME localized its
> Assist screen and mapped seven field labels; JIM localized its
> Channel & camera screen. Nothing new crosses into the vault.

## app-v0.44.2 — PDI app-v0.44.2

- Published: 2026-08-05
- Commit: `22d625aba20549c39746dfa7a8ad4170dffd2634`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.2>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones
> gained the last doors: genesis and hybrids, packs, simulations,
> the contribution ledger, proactive reach, licensing and the senses,
> and the per-shell doorless records run to zero. Nothing new crosses into the vault.

## app-v0.44.1 — PDI app-v0.44.1

- Published: 2026-08-05
- Commit: `f2113f726b4ba9e3416a4d1dbb6f2df523e0d4fa`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.1>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones
> gained the sticker, the queue and the stamp: beacons/QR and pairing,
> moderation with message edit and retract, reviews, watermarks, media
> and wearables, 24 routes with doors on iOS, Android and Windows. Nothing new crosses into the vault.

## app-v0.44.0 — PDI app-v0.44.0

- Published: 2026-08-05
- Commit: `15b57eb955bd3db147d9041d8785af372414ef4e`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.44.0>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones
> gained the keys, the till and the lifeline: accounts, money and
> status+help, 24 routes with doors on iOS, Android and Windows. Nothing new crosses into the vault.

## app-v0.43.9 — PDI app-v0.43.9

- Published: 2026-08-05
- Commit: `a42dbe77ae32c5e1891781f20f267ae1b28d1204`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.9>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones
> gained the face round: portrait, emblem and badge, page and themes,
> front, surfaces, blend, bodies, dials and the wrist, 24 routes with
> doors on iOS, Android and Windows. Nothing new crosses into the vault.

## app-v0.43.8 — PDI app-v0.43.8

- Published: 2026-08-05
- Commit: `23d029afd0249710667e09e94b6a823166f70ba3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.8>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — JIM's watch bridge
> gained the device picker (Apple Watch, Wear OS, Fitbit, Garmin), the
> Fitbit-aware seed, and Bluetooth pairing for speakers, glasses, AR/VR
> headsets and spatial displays. Nothing new crosses into the vault.

## app-v0.43.7 — PDI app-v0.43.7

- Published: 2026-08-05
- Commit: `06212ad7523ee7e3a63562b030f71165e9a471c0`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.7>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> the memory list, the pair's record, source material, the ledger,
> anonymity, verification and the profile's three endings, striking 75
> rows from its per-shell doorless records. Nothing new crosses into the vault.

## app-v0.43.6 — PDI app-v0.43.6

- Published: 2026-08-05
- Commit: `d2ffcbf241fc7edc87dfddac62f50713b56ddf62`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.6>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> workflows, delegation, the assistant, tasks under a grant, rated
> placements and specialists, striking 84 rows from its per-shell
> doorless records. Nothing new crosses into the vault.

## app-v0.43.5 — PDI app-v0.43.5

- Published: 2026-08-05
- Commit: `6504b431620bda524f30154ce4a9d61d015f29eb`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.5>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> signatures, mail settings, rooms, wall screens, memberships, handoffs
> and campaigns, striking 74 rows from its per-shell doorless records.
> Nothing new crosses into the vault.

## app-v0.43.4 — PDI app-v0.43.4

- Published: 2026-08-05
- Commit: `d9564309e47d51c0294ae16ada3e9054fe313219`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.4>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> the robot body's audit trail, the referral flow, objections, the game
> lobby and the helper dock, striking 75 rows from its per-shell
> doorless records. Nothing new crosses into the vault.

## app-v0.43.3 — PDI app-v0.43.3

- Published: 2026-08-05
- Commit: `b51d54b28d5c06ec4533d593da067c59f0162101`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.3>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> the place disclosures, the camera, organizations and the guided tour,
> striking 81 rows from its per-shell doorless records. Nothing new crosses into the vault.

## app-v0.43.2 — PDI app-v0.43.2

- Published: 2026-08-04
- Commit: `4f9ad74e824490f781ff366f891d725c647c52f3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.2>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME's phones gained
> the audience verbs, the watch party and skill grants, striking 84 rows
> from its per-shell doorless records. Nothing new crosses into the vault.

## app-v0.43.1 — PDI app-v0.43.1

- Published: 2026-08-04
- Commit: `1cf80269eaf5b10679ae8d4066f37b8caaaa2068`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.1>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME gained an inbox
> that tells a person what was done to them. Nothing new crosses into
> the vault.

## app-v0.43.0 — PDI app-v0.43.0

- Published: 2026-08-04
- Commit: `0f895c2b229bfead8fa209481d9cfa849857fa06`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.43.0>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. QRME's phones learned to staff a desk, trade in the market
> and sign an exchange. Nothing new crosses into the vault.
>
> ### The guard learns to read a Swift verb
>
> QRME's round exposed a rule this repo shares: the iOS route audit read
> only the `request(` helper, so a URL built with `appendingPathComponent`
> and sent through a raw `URLRequest` was invisible to it. This shell has
> exactly one such call — `submitIntake`, the door an invited sender walks
> through — and the audit had it listed as work to do.
>
>     asked     does the shell call the transport helper for this route
>     mattered  does the shell fetch this route at all
>
> The rule arrives with its premise: the verb is read from `httpMethod`,
> never assumed, because QRME's first draft assumed GET and its own suite
> falsified that within the hour. `POST /intakes/{iid}/submit` comes off
> the ios doorless record — a row that was never work at all.

## app-v0.42.9 — PDI app-v0.42.9

- Published: 2026-08-04
- Commit: `83ba3b9520e2f888ca78ab4dfaca9a0c3bb65e5e`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.9>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — QRME's friends list, wall and
> comments gained doors on its three native shells. Nothing new crosses
> into the vault.

## app-v0.42.8 — PDI app-v0.42.8

- Published: 2026-08-04
- Commit: `4e457a0481ab2b86219df9e1e903a58dfffff007`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.8>

> ### Version alignment
>
> The three products are cut together, so one number names one
> combination of all three. No PDI code changed — QRME and JIM audited
> their field-label records against their consoles' actual forms and
> labelled the 161 fields the forms had started asking for.
>
> ### The vault gets its light
>
> The sibling consoles' always-on lights widget, sized down to what this
> product honestly has to glance at: one lamp, bottom-left, green while
> the vault answers — with its version beside it, so a stale backend is
> visible at a glance. Reads `/health`, the open route the version guard
> already reads, so nothing new owes a door. Minimizable to a dot, and
> unreachable is a state it shows: an unlit dot that retries on press,
> never a silent absence.

## app-v0.42.7 — PDI app-v0.42.7

- Published: 2026-08-04
- Commit: `c5eacf9e02a82dc694b9b2052f84ee22bd85f6c3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.7>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — QRME's people gained friends-only
> messages, feature switches and a homepage sandbox, and JIM's users
> gained the same surfaces inside their own deployment. Nothing new
> crosses into the vault.

## app-v0.42.6 — PDI app-v0.42.6

- Published: 2026-08-04
- Commit: `53cc584694ac8876e69cf1c585fba29f9bbe7ee4`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.6>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — JIM gained booking and scheduling
> with reminders on its proactive ladder and opt-in email to the user's own
> verified address; nothing in an appointment row or a reminder crosses into this vault, and nothing needed to.

## app-v0.42.5 — PDI app-v0.42.5

- Published: 2026-08-04
- Commit: `9e6f1dbcb66fdf6f525f5a60068f48797b81bbee`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.5>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — QRME grew standalone shops and JIM
> grew the buyer's side in this round; the purchase histories those buyers
> keep live in JIM's own tables, exactly as this vault's custody rules
> would have demanded had anyone asked.

## app-v0.42.4 — PDI app-v0.42.4

- Published: 2026-08-04
- Commit: `7dbf5eb6a573d1f8168aaba5ed76e15d09eb0ff6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.4>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — JIM's money guardian gained its
> native doors on iOS, Android and Windows in this round, and the account numbers those phones register still land here, sealed, or nowhere.

## app-v0.42.3 — PDI app-v0.42.3

- Published: 2026-08-04
- Commit: `af127a2d9db01e9bfd5b25471ff25abba767a840`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.3>

> ### The last thirteen unaudited screens
>
> Five components had sat `unaudited` in `ui_screens.txt` since the manifest
> was seeded. `Records` heads itself "Vault" and was only unlabelled —
> screens **2** and **3** draw it — and the other four had never been drawn
> at all: Continuity, Operations, Positions and Settings, each iterated on
> for versions with nothing in the gallery.
>
>     asked     is every component accounted for in the manifest
>     mattered  does every component have a drawing
>
> Screens **53 Continuity** (bequests and the gateway's ceiling), **54
> Operations** (the sealed coordination journal, readable in place), **55
> Positions** (the role questionnaire and its assistant blueprint) and **56
> Settings** close the column. Both ceilings now read zero and the slack
> test keeps them there.

## app-v0.42.2 — PDI app-v0.42.2

- Published: 2026-08-04
- Commit: `2d6ecbaa0692d9a2a659ba956f50dfa80997dbc0`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.2>

> ### Version alignment
>
> The three products are cut together, so one number names one combination
> of all three. No PDI code changed — but this is the round the vault was
> built for: JIM's new money guardian seals account numbers, routing numbers
> and exchange keys here, and refuses to store them anywhere else.

## app-v0.42.1 — PDI app-v0.42.1

- Published: 2026-08-04
- Commit: `7e0554e6114f28937eb652331c6f24602407d909`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.1>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed in this round: QRME's Starter Collection
> gained per-starter dossiers — knowledge, skills and connections.

## app-v0.42.0 — PDI app-v0.42.0

- Published: 2026-08-04
- Commit: `e1444dfeff7c51de751932e922074259024742e2`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.42.0>

> ### Version alignment
>
> The three products are cut together, so one number names one combination of
> all three. No PDI code changed in this round: QRME gained desk service
> connections (sessions, consent-first access offers, tokens that die with
> the link), and JIM-mini's monitor door now carries the device's own
> signal-quality report to the grader.

## app-v0.41.0 — PDI app-v0.41.0

- Published: 2026-08-02
- Commit: `11396a2f264946947f1a948efe8414119d48ffa6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.41.0>

> ### The workflow round-trips and nothing walked the whole arc
>
> ### The finding
>
> The cross-product smoke check boots QRME, JIM-mini and PDI together, seeds all
> three, and proves an exchange is sealed in the vault with its provenance
> readable back through JIM's custody window. It stopped there. The multi-phase
> arc that sits on top of that exchange — a goal handed to a synthetic
> specialist, worked over several phases, paused for a human at `confirm` — was
> never walked, so the vault's part in it was never driven either.
>
>     asked     does the workflow round-trip
>     mattered  does anything walk the whole arc
>
> ### What driving it found
>
> The arc now runs to `confirm` in the same process as a live PDI tenant, with
> the specialist's `research` phase scoped by a grant rather than reading
> whatever it likes. That is the property this product exists for, and it is now
> exercised by a run rather than only by PDI's own unit tests: a delegated phase
> reads what a grant permits, and a revoked grant halts the workflow.
>
> ### This release
>
> Version alignment: the three products are cut together, so one number names one
> combination of all three. No PDI code changed in this round; the check that
> drives it did.

## app-v0.40.9 — PDI app-v0.40.9

- Published: 2026-08-02
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.9>

> ### The README said v0.18.0
>
> ### The finding
>
> The first bold line of every README in all three products read:
>
>     **Current release: v0.18.0**
>
> and the line directly beneath it said the three are *"versioned and cut
> together, so one number names one combination of all three"* — a convention the
> banner had stopped following at 0.18.0 and kept advertising for twenty-two
> releases.
>
> The release-history table underneath stopped at **0.30.6**. Seventeen shipped
> releases — 0.25.0 through 0.29.0, 0.30.7 to 0.30.9, and the whole 0.40.x line —
> were in `CHANGELOG.md` and absent from the page anybody actually reads. The
> changelog was right the entire time; the summary of it in front of the door was
> behind.
>
>     asked     is the release written down
>     mattered  does the front page say what shipped
>
> Reported from the README beside the video, which is the one place this was
> always going to be noticed and the one place no test was looking.
>
> ### Changed
>
> - The banner names `pyproject.toml`'s version; the table carries every release
>   from 0.25.0 on, backfilled from each product's own changelog.
> - `test_the_readme_says_what_shipped.py` — five tests, the same file in all
>   three: the banner matches the version, every release has a row, the newest
>   row is this release, no row names a release that was never cut, and a guard
>   on the scan itself.
>
> Two injections, both reproducing the reported defect exactly: the banner set
> back to v0.18.0, and the table truncated at 0.30.6 again.

## app-v0.40.7 — PDI app-v0.40.7

- Published: 2026-08-02
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.7>

> ### The record that outlived the code
>
> ### The finding
>
> `public_untranslated.txt` opened with a paragraph explaining that
> `Onboarding.tsx` — the screen every person in the world meets first — carried
> forty-odd English strings, that translating them was "its own round", and that
> a half-translated sign-up form would be worse than an English one. All of that
> was true when it was written.
>
> `The screen everybody meets first` translated them. `The pre-session backlog
> reaches its floor` took the count to four and appended its correction *below*
> the stale paragraph, which nobody struck:
>
>     What is left is not prose. A product name, a punctuation mark, an
>     example address and an example code — strings that are the same in
>     every language. This is the floor, not a backlog.
>
> So the file held two statements about itself with the false one first. Read
> top-down — which is how anybody reads a file — it advertised a cleared backlog,
> and the correction was twenty lines further on. This round was planned off that
> paragraph before the extractor was run and the work turned out to be two
> releases old.
>
>     asked     is the record complete
>     mattered  does the record still describe the code
>
> The numbers were right the whole time. The prose around them had outlived the
> thing it described, and a record only works if a reader can trust the first
> thing it says.
>
> ### Every ratchet now leads with what it is
>
> `# status: floor|backlog — N rows`, on the first line, with the count checked
> against the rows beneath it. `floor` means the remainder is permanent and is
> not work; `backlog` means somebody still owes it. The two cannot be told apart
> from the numbers — `console_untranslated` sits exactly at its ceiling with
> 1,459 strings still to translate, and `public_untranslated` sits exactly at its
> ceiling and is finished — which is why the file has to say which it is, in a
> line that cannot drift from its own contents.
>
> A third check was written and struck before it shipped: *a file calling itself
> a floor must sit exactly at its ceiling*. It fired on `native_untranslated.txt`,
> which the last release took from three rows to none — a floor of zero under a
> ceiling of three, and the best kind there is. `floor` is a claim about what the
> remaining rows **are**, not how many, and a check that pretended otherwise
> would have been one more guard answering the question next to the one that
> matters.
>
> ### The reasons move next to the rows
>
> `unused_native_bindings.txt` recorded two bindings whose justification lived in
> the guard's module docstring — true, careful, and one file away from the list
> it explained. A record whose justification is somewhere else reads, at the
> place somebody actually looks, as an unexplained backlog: the shape this audit
> found seven times in `0.40.5`. Every row now carries its reason on the row, and
> a new check refuses one that does not.
>
> ### Changed
>
> - `tests/test_a_record_that_outlived_the_code.py` and the binding-reason check,
>   both shared byte-for-byte with the sibling products.
> - Status lines on both ratchets here.
>
> This product's `unused_native_bindings.txt` is empty and its refusal record
> sits at its declared floor of one, so the checks land on a repo that already
> had nothing to correct — which is the right time to add them.

## app-v0.40.6 — PDI app-v0.40.6

- Published: 2026-08-02
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.6>

> ### Cut alongside qrme and jim-mini
>
> No change in this product. The round finishes localizing QRME's **accountless
> screen** — the one built for somebody who has found a synthetic profile of
> themselves and has no account, and therefore no profile language to take a
> setting from.
>
> This product's accountless readers — a bequest grantee, an intake recipient — meet it through the console rather than a native shell, and `test_the_vault_refuses_in_one_language.py` already holds that surface to the reader's language. No native screen here is built for somebody without a tenant.
>
> The shells here already resolve a device language and already send it as
> `accept-language`; what they do not have is a screen whose reader provably has
> no profile. Recorded rather than left silent: a version where all three move
> together and one is untouched should say which one and why.

## app-v0.40.5 — PDI app-v0.40.5

- Published: 2026-08-02
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.5>

> ### Every door of theirs answered 401; the grantee's answered with the record
>
> `vault.tenant_by_id` has carried its qualifier since it was written, and says
> so in its own docstring:
>
> ```sql
> SELECT * FROM tenants WHERE id=? AND deleted_at IS NULL
> ```
>
> > tenants (deleted_at set) resolve to None — their data is unreachable
>
> `bequests.py` did not use it. It resolved the tenant twice with its own
> `SELECT * FROM tenants WHERE id=?` — no qualifier, no `_scrub`. Driven end to
> end against a tenant who deleted their vault:
>
>     DELETE /tenants/{id}?mode=soft            200
>     GET /records/{key}      (owner's token)   401  access cut
>     GET /bequests/grant/keys                  200  ["jim/u1/medical/note"]
>     GET /bequests/grant/read?key=...          200  {"value": "a private note"}
>
>     asked     can the tenant still reach their vault
>     mattered  can anyone still reach it
>
> Soft-delete is the *recoverable* one — a tombstone with a window — which is
> exactly why nothing about it looks like an emergency, and why the door it left
> open stayed open quietly. A grantee holding an activated bequest read the
> plaintext of a vault whose owner had closed it.
>
> On `mode=wipe` it was worse than open: the tenant row is deleted outright, so
> the same line evaluated `dict(None)` and the grantee met a **500** rather than a
> refusal. The wipe also retired `tenant_tokens` while leaving the `bequests` rows
> themselves — a live grant hash against a tenant that no longer existed.
> `delete_tenant` says it removes "the tenant's records, scoped tokens, and the
> tenant row"; the bequest grant is a scoped token that lives in a different
> table.
>
> ### Changed
>
> - Both tenant lookups in `bequests.py` go through `vault.tenant_by_id`, so the
>   path that answers a stranger asks the same question every other door asks.
>   A closed vault answers 410 with a sentence in the reader's language; a
>   restored one opens again.
> - `vault.delete_tenant` revokes the tenant's bequests and clears their grant
>   hashes on a wipe.
> - `pdi/tests/test_the_grant_outlived_the_vault.py` — nine tests, including a
>   structural one that fails any tenant lookup in the bequest path that ignores
>   the tombstone, wherever in the file it sits: the two that were wrong were in
>   two different functions, and naming them would have been the same mistake a
>   second time.
>
> The sibling products had the same class in their own idiom, and the same round
> landed in all three: in QRME a terminated profile was still being licensed and
> cloned through the buyer's token, and in JIM-mini an erased account's watch
> channel was still depositing readings.

## app-v0.40.3 — PDI app-v0.40.3

- Published: 2026-08-02
- Commit: `189d57c190693756365d57037075f88bf010882d`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.3>

> ### Cut alongside qrme and jim-mini
>
> No change in this product. The round is about what a model-backed product says
> when the model it was asked for does not answer, and PDI has no inference path
> of its own — it stores what the other two seal.
>
> Recorded rather than left silent: a release where all three move together and
> one of them is untouched should say which one and why, or the next reader has
> to diff three repositories to find out.

## app-v0.40.2 — PDI app-v0.40.2

- Published: 2026-08-02
- Commit: `b091b06450c7b298f5d3618e2f8211e1859592b3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.2>

> ### The refusals, finished
>
> 0.24.0 translated the eleven refusals any route can raise and **wrote the rest
> down**. 49 sentences sat in `pdi/tests/refusals_untranslated.txt` from that day to this — the sentences
> the vault says when it says no, still English on an account that had chosen
> otherwise.
>
> The reader most exposed here never chose English or anything else: the
> recipient of a handoff, holding a submit token and no account.
>
>
>     asked     is the refusal translated
>     mattered  is every refusal translated
>
> All 48 are now in `_REFUSALS`, in the nine languages beside English. The
> record is a decision rather than a backlog for the first time: one sentence, the `PDI_ADMIN_TOKEN` misconfiguration its own header already
> argued should stay English.
>
> ### What deliberately stays an identifier
>
> Field names, header names, enum values and environment variables are not
> translated and are not meant to read as words — `x-tenant-key, handle, soft/wipe`. They are the API's own
> names, the same string in every language, and declining them into a sentence is
> the half-in-one-language failure the table exists to refuse.
>
> ### The check that could not have caught a lie
>
> `test_every_translated_refusal_has_every_language` asks whether each row has
> all nine keys. A row whose nine values are the English sentence pasted nine
> times satisfies it exactly — and the table would then claim the refusal is
> handled while every reader still got English.
>
>     asked     does every refusal have every language
>     mattered  does every language say something other than the English
>
> That gap was harmless while eleven rows were added by hand and reviewed one at
> a time. It stops being harmless the moment 48 are added in one release, so
> `test_no_refusal_is_translated_into_english` was added first and injected
> against: an English value in one slot of one row fails it by name.

## app-v0.40.1 — PDI app-v0.40.1

- Published: 2026-08-02
- Commit: `8732ee0f2a313cd83448bb36f406eed75b73fae6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.1>

> ### The language no client was sending
>
> PDI's most exposed reader has no account by design: the person on the other end
> of a handoff, opening an intake with a submit token and nothing else. The pages
> and refusals they meet are composed by the backend, sentence by sentence, and
> every one of those sentences is chosen from `Accept-Language`.
>
> **No native shell was sending that header.** The browser sends it without being
> asked, which is why the console looked correct and the recipient on a phone —
> the person this product exists to hand something to — was the one being
> answered in English.
>
>     asked     can the shell say it in the reader's language
>     mattered  does the reader's language ever reach the server
>
> Two things were missing. There was **no language to send**: each shell's
> `language` comes from the stored tenant setting and is `"en"` until a tenant
> exists. `L10n.deviceLanguage` (iOS), `L10n.deviceLanguage()` (Android) and
> `L10n.DeviceLanguage()` (Windows) now read `Locale.preferredLanguages`, the
> system configuration's locale list and `CurrentUICulture`, drop the region, and
> fall back to English rather than guessing. Then there was **somewhere to send
> it** — and in this product that is two places per client, not one: the shared
> request helper *and* the intake submit, which builds its own request because it
> carries a submit token instead of a bearer.
>
> That second path is the recipient's. A fix that had only covered the shared
> helper would have localized everything except the surface this round is about.
>
> ### The guard reads every request path, not one of them
>
> `test_the_language_nobody_was_sending.py` first asked whether *any* header line
> carried the device resolver. Hardcoding `"en"` on the intake path passed it,
> because the shared helper was still right — the union hiding a surface inside
> the guard written to stop exactly that. It checks every line now.
>
> ### Windows' localizer takes a language now
>
> `L10n.T(key)` read `AppState.Current.Language` and had no way to be told
> otherwise. A `T(key, lang)` overload closes the gap; iOS and Android already
> required the language as an argument.

## app-v0.40.0 — PDI app-v0.40.0

- Published: 2026-08-02
- Commit: `d4347e593067289226594b469fcf178f439fb19f`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.40.0>

> > Staged as 0.30.10 and cut as **0.40.0**. The work below is unchanged; only
> > the number moved, from a patch on the 0.30 line to a minor of its own.
>
> ### Version alignment
>
> The three products are cut together at one version, and this release's work is
> in the siblings.
>
> **JIM-mini**: a QRME specialist could be reached from the monitoring path and
> not from the coach — the person whose watch noticed something got the better
> answer than the person who sat down and typed the problem out. That is now
> bridged, as an *offer* rather than an automatic route, because what would cross
> the tandem is what the person wrote rather than a sensor finding.
>
> **QRME**: its console language record was overstating itself by 117 rows of
> punctuation, kept under a stated rule — *"a separator somebody reads"* — that
> conflated *rendered* with *unreadable to a non-English speaker*. Corrected, and
> the reversal is written down rather than made quietly.
>
> This repo's own language record was corrected the same way one release ago, and
> its transfers surface remains the subset that should come off those numbers
> first.

## app-v0.30.9 — PDI app-v0.30.9

- Published: 2026-08-02
- Commit: `ae99e52db7cc7d01951f766d2dd7282ec1d4dd23`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.9>

> ### An HTTP verb where a path goes
>
> This product's Android client declares its shared helper
> `request(path, method, body, token)`. The `offlineStatus` call added in
> 0.30.7 passed them the other way round — `request("GET", "/offline/status", …)`
> — so the vault was asked for `base + "GET"` with the method set to a path.
>
> Both arguments are `String`. Nothing complained, there is no Kotlin toolchain
> in this build environment, and the offline posture card on Android has been
> reading a 404 since it shipped.
>
>     asked     does the call have the right number of arguments
>     mattered  does it have them in the right order
>
> Fixed, and guarded: `test_a_screen_nothing_opens.py` now reads the helper's own
> declared signature and refuses an HTTP verb in the path slot. It was found by
> the route-door guard rather than by anything looking for it, and only because a
> DELETE went missing from a backlog in the sibling repo.
>
> ### Last release's untranslated counts were overstated
>
> 0.30.8 measured how much of each native shell is English behind a translated
> tab bar. The extractor counted **any string literal containing a letter**,
> which counted format fragments like `"${dim}: ${n}%"` — whose only letters are
> variable names nobody reads — as English prose.
>
>     asked     does this literal contain letters
>     mattered  does this literal contain words a reader reads
>
> The ratchet caught it by firing on a card in the sibling product that had just
> been fully localized. Corrected figures, now in
> `native_screens_untranslated.txt`:
>
> | shell | was recorded | actually |
> |---|---|---|
> | iOS | 92 | **88** |
> | Android | 79 | **75** |
> | Windows | 138 | **119** |
>
> Restated percentages for this product: 9.3% / 10.7% / 4.0%. The finding is
> unchanged — the vault's tab bar reads *Bóveda*, *Auditoría*, *Transferencias*
> and the screens behind them are English — and the transfers surface is still
> the one that should come off these numbers first.

## app-v0.30.8 — PDI app-v0.30.8

- Published: 2026-08-02
- Commit: `d1c86feb64963d56e78df4c07cb17edfc1b93f95`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.8>

> ### The tab bar answers in your language. Everything behind it does not.
>
> The QRME repo has carried a console guard since those rounds —
> `test_the_nav_is_translated_and_nothing_behind_it_is.py` — which found
> forty-six translated sidebar labels in front of 1577 English screens, and said
> why that is worse than shipping no translations at all: a uniformly English app
> tells a Spanish reader the truth on the first screen; a translated nav in front
> of English screens tells them the opposite and then hands them English anyway.
>
> Three products ship three native shells each. All nine have a translated tab
> bar. Nobody had ever counted what is behind them.
>
> | product | iOS | Android | Windows |
> |---|---|---|---|
> | QRME | 2.4% | 3.8% | 0.6% |
> | JIM-mini | 13.0% | 14.2% | 9.7% |
> | **PDI** | **8.9%** | **10.2%** | **3.5%** |
>
>     asked     is the console's nav-vs-behind gap measured
>     mattered  is the phones' too
>
> The vault's tab bar reads *Bóveda*, *Auditoría*, *Transferencias*. The screens
> behind them are English. `native_screens_untranslated.txt` now records 92 iOS,
> 79 Android and 138 Windows strings, ratcheted in both directions — the count
> may not rise, and the record may not sit more than twenty above the real
> number, so the ceiling cannot quietly become somewhere to drift back up into.
>
> ### Nothing is carved out here yet, and the record says which surface should be
>
> The sibling product took its **alarm surface** off these numbers this release —
> fourteen strings on all three of its shells, by name rather than by count,
> chosen because that is where English is a hazard rather than a discourtesy.
>
> This repo has no equivalent subset yet. The record names the candidate rather
> than leaving the absence implicit: the **transfers** screens, which move sealed
> records to another party. Those are the ones where not understanding changes
> what happens rather than merely what is known.
>
> ### Every slot is now checked to survive its translation
>
> A row whose English says `{name} was contacted` and whose German forgot the
> hole renders a sentence with the person's name missing from the middle of it.
> The string is present, the language is right, and the sentence is wrong.
>
> Where a shell's table holds no slotted row — which is all three here today —
> the check **skips loudly** rather than passing on an empty set. A check over
> nothing is the failure mode this audit is named after, and a skip says so in
> the run output where a green dot would not.

## app-v0.30.7 — PDI app-v0.30.7

- Published: 2026-08-02
- Commit: `40b3e2c9f561d8b9c4856593990cf08a6f4b414e`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.7>

> ### Offline mode became readable
>
> `PDI_OFFLINE` refuses anything bound for another machine, and until this
> release a deployment could set it and had no way to show anyone the result.
> `GET /offline/status` now reports the posture — whether external transmission
> is possible, what counts as a local destination, what is guaranteed while the
> flag is on — and it is on screen: a panel in the console's Settings, and a card
> at the top of Overview in the iOS, Android and Windows shells.
>
> Read-only on purpose. The posture is set in the deployment's environment, not
> by somebody signed into the vault, and a switch there would imply otherwise.
>
> ### A guard ported before this repo needed it
>
> `test_a_screen_nothing_opens.py` holds every screen a shell declares to being
> reachable from somewhere in that shell, and every call to that shell's
> localizer to the number of arguments the localizer actually declares.
>
> The finding is the sibling product's: a screen shipped into three shells with
> its wording in ten languages, unreachable in all three, and on two of them
> written against a signature it did not have.
>
>     asked     does the screen have its wording
>     mattered  does anything open the screen
>
> This repo's shells are clean of both. That is the point of porting it now —
> the four rounds before this one each found a guard covering one surface of
> four, and the surfaces here are the same three shells written the same way.
>
> What the port did surface here is smaller and left standing rather than fixed
> under cover of a round about something else: this product's Windows shell makes
> exactly two localizer calls, where its iOS and Android shells make more, and
> the reason is recorded on the guard rather than papered over by raising its
> floor.

## app-v0.30.6 — PDI app-v0.30.6

- Published: 2026-08-02
- Commit: `e0fbc13b0290c71e836482efe50282a63882da38`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.6>

> ### The plan gate speaks the reader's language
>
> `refusals_untranslated.txt` carried this as an exception for four releases, in
> its own words: a template whose slots were English prose, where translating the
> frame alone would produce *"a sentence half in each language, at the one moment
> in this product that stands between somebody and a decision to pay"*.
>
>     asked     can the frame be translated
>     mattered  can the slots be
>
> They can — where the sentence exists.
>
> PDI has no plan gate, so there is no sentence of this shape to translate here.
> The release carries the version alignment and the sibling audit; the mechanism
> that would catch it — the `Term` exemption paid for by a vocabulary check — is
> already in place from the previous release.

## app-v0.30.5 — PDI app-v0.30.5

- Published: 2026-08-01
- Commit: `e6c2cc961ef31efb178133888ef01bfdf48bcf9c`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.5>

> ### The plan gate said HTTP 402
>
> 0.30.4 left the plan gate open as the one refusal deliberately not translated,
> because its message interpolates prose. Going back to translate it turned up
> something else first: on three of the four client families it was not arriving
> at all.
>
> `detail` has three shapes in this product — a **string** for most refusals, a
> **dict** for the plan gate, a **list** for a 422. 0.30.3 gave the list a
> top-level `message` and taught every client to read it. The plan gate's
> `message` stayed nested inside its dict.
>
>     asked     does the sentence ride beside the structure
>     mattered  does every structured refusal put it in the same place
>
> The three native shells look for a top-level `message`, then for a string
> `detail`. A dict is neither, so the one refusal in this product that stands
> between somebody and a decision to pay rendered as the bare status code: no
> price, no plan name, no reason.
>
> | Client | Before | After |
> |---|---|---|
> | iOS | `HTTP 402` | the sentence, with price and plan |
> | Android | `HTTP 402` | the sentence, with price and plan |
> | Windows | `HTTP 402` | the sentence, with price and plan |
> | Console | correct | unchanged |
>
> **One of those was a regression from 0.30.3.** Android had been coercing the
> dict through `toString()` and showing its raw JSON — ugly, but it contained the
> price. Teaching it to read the top-level key first is what dropped it to the
> status code. iOS and Windows had always been broken.
>
> **The fix is not a third special case.** Every refusal now carries a top-level
> `message` holding the sentence a person reads, whichever shape `detail` is, so
> a client never has to know the shape and a structured refusal added later
> cannot repeat this. `detail` is untouched: the console still reads the dict to
> draw the upgrade card with its price and button. `sentence_of` returns nothing
> when there is nothing readable rather than inventing a sentence — a bare status
> is more honest than one this codebase made up, and would be indistinguishable
> from a real one.
>
> **A second defect underneath it.** `localize_detail` looked one level down, and
> `api.py` wraps every `HTTPException` as `{"detail": exc.detail}` before it
> runs — so a structured refusal arrives two levels down and its sentence went
> out **untranslated in every language**.
>
>     asked     is a structured refusal localized
>     mattered  is it localized where the wrapper actually puts it
>
> Found because the new translation check failed rather than passed, which is
> what it was written to do. PDI has no structured refusal today; the branch is in place so the first one does not ship untranslated, which is how it happened in the sibling.

## app-v0.30.4 — PDI app-v0.30.4

- Published: 2026-08-01
- Commit: `9b1f0f98026c1e29f3648ef37bd131a8880f9df6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.4>

> ### A refusal whose English is not a constant
>
> `refusals_untranslated.txt` has carried the same paragraph for three releases:
> f-string refusals, named as uncovered and deliberately not counted in the
> backlog, because
>
>     f"language must be one of {', '.join(SUPPORTED)}"
>
> cannot be looked up by its English source — at the moment it is raised there is
> no English source, only a result.
>
>     asked     is the refusal a constant we can translate
>     mattered  is every part of it something we can translate
>
> `i18n.Templated` is a `str` whose value is the finished English sentence,
> carrying the template and its slots so `localize_detail` can refill the frame
> in the reader's language. Nothing that already treats a detail as text changed
> — the default English path, JSON encoding, and every driven test asserting on a
> refusal message all work exactly as before.
>
> **The slot is the whole design.** A translated frame around an English slot is
> *worse* than an English sentence: it reads as a bug, in front of somebody who
> is already being told no. That is precisely why this record refuses to ship a
> translated plan gate, and doing it here by accident would have been the same
> mistake with a mechanism to spread it. So whitespace means prose, and a slot
> that fails the test keeps the whole refusal English — the state it was already
> in, now chosen rather than stumbled into.
>
> The known limit is stated rather than hidden: a **single** English word has no
> whitespace either, and is indistinguishable from an identifier.
>
> PDI has no refusal that interpolates a closed set, so it carries the
> mechanism without QRME's `Term` marker and vocabulary, and the guard fails if
> that stops being true. **4 sites converted**, 26 remaining.
>
> The extraction read this product's own test file as a raise site, because tests
> live inside the package here and beside it in QRME — caught by the literal-slot
> check firing on its own examples.

## app-v0.30.3 — PDI app-v0.30.3

- Published: 2026-08-01
- Commit: `3dc436fd056e28da876427fbe9adad4bdd0d4376`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.3>

> ### The refusal that arrived as a list
>
> 0.30.1 put the 422 into the reader's language — the refusal a mistyped form
> produces, and the one a person meets most often. Nothing looked at what a
> client does with the result.
>
> `detail` on a 422 is a *list* of pydantic rows, and every client family
> rendered it by a path written for a string. The console called
> `JSON.stringify` on it, so the note under a form read
> `[{"type":"missing","loc":["body","display_name"],"msg":"Field required"}]`.
> Android's `JSONObject.optString` coerces a `JSONArray` through `toString()`,
> producing the same. iOS asked for `as? String`, got `nil`, and fell back to
> `HTTP 422`; Windows called `GetString()` on an array, which throws, was
> caught, and did the same.
>
>     asked     is the refusal translated
>     mattered  is the refusal a sentence
>
> The `msg` translated last release was correct, arrived, and was read by
> nobody: it sat inside a JSON blob or was discarded for a status code. Two of
> the four families showed the person **less** than before their language was
> ever considered.
>
> **The fix.** `i18n.validation_message` composes one sentence from the rows, in
> the reader's language, and rides beside `detail` rather than replacing it —
> `detail` is the FastAPI contract, what a machine reading this API has a right
> to, and what the driven tests read. Every client decode now reads the sentence
> first. The field name stays the API's own (`display_name`), joined with an em
> dash rather than declined into the sentence, so nothing comes out half in one
> language and half in another. Mapping those names to the labels a form
> actually shows needs a per-client table that does not exist, and is recorded as
> the remaining gap rather than guessed at.
>
> **The guard took three attempts, and the first two are why the third is worth
> having.** Asking whether a client's source mentions `message` passed on all
> four clients while all four were broken — it is a field on a model, a
> parameter name on an exception class, and a word in the comment directly above
> the bug. Anchoring on the throw and asking whether the surrounding lines read
> it caught the three shells and still passed on a broken console, because the
> fallback chain has always read the sentence key as an *alternative to*
> `detail`.
>
>     asked     does the decode mention the sentence
>     mattered  does the decode pass the sentence on
>
> Seven injections, each caught by the right test with the right message.

## app-v0.30.2 — PDI app-v0.30.2

- Published: 2026-08-01
- Commit: `ba53dbf5b0b275bd14f93e6aa05d428101701aba`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.2>

> ### The synthetic self enters the tandem contract
>
> `docs/tandem.md` gains the boundary before the code that obeys it, and this
> release carries the amendment that names the one exception to it. The
> implementation is JIM-mini's and the profile is QRME's; the contract is shared,
> byte-identical in all three repositories, which is why it lands here too.
>
> PDI's stake in it is the destination. The brief the guardian composes arrives
> through QRME's owner-gated `POST /profiles/{id}/sources`, and QRME seals source
> material into its PDI vault when one is configured — so a person's medication
> names, if they consent to that category, come to rest encrypted here rather
> than beside the profile.
>
>     asked     does JIM reference synthetic profiles
>     mattered  does JIM reference this person's own
>
> The rule the vault inherits: an enumerated allowlist, consented per category,
> empty by default, with the composer building the brief *from* the allowlist
> rather than filtering a payload down to it. Journal entries, check-in notes and
> transcripts never cross under any consent. Medication is the one category made
> of the person's own words, named in the contract rather than left to an
> implementation, because a drug name somebody typed can be a diagnosis.

## app-v0.30.1 — PDI app-v0.30.1

- Published: 2026-08-01
- Commit: `01e3f49379080a8964dfa6b873a34d25fa1260e3`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.1>

> ### Isolation held, and nothing was checking it
>
> Driven rather than read: the whole GET surface, seventy routes, as a second
> tenant against a first tenant's seeded records, transfers, bequests, beacons
> and positions. **No cross-tenant read.** The mutating routes driven the same
> way, including the compliance record. **No cross-tenant write.**
>
> So this release does not close a hole. It closes what was missing: there was no
> test of any of it. Isolation is the one property this product exists to
> provide, and it was true by the care of whoever wrote each route, with nothing
> to say so the day one of them is written differently.
>
> **Why nobody would have noticed.** `_LOCAL_CALLERS` contains `"testclient"`,
> and `_admin` treats a local caller as authorised when `PDI_ADMIN_TOKEN` is
> unset. Every other test in this suite runs with the admin surface wide open.
>
>     asked     is the admin surface refused
>     mattered  is it refused to somebody the harness is not
>
> Run that way, a tenant appears to file a Business Associate Agreement on
> another tenant's account and get `201` — the harness authorising itself as the
> operator, not a cross-tenant write. Configured, and driven from an address that
> is not this machine, it is `403`; an unconfigured deployment answers `503` to
> the network rather than opening. Both are asserted.
>
> The sweep collects **crashes as well as leaks**. Record ciphertext is sealed
> with associated data of `f"{tenant_id}:{key}"`, so a query that forgets its
> tenant scope does not return another tenant's value — it fails to decrypt and
> raises `InvalidTag`. Real defence in depth, and exactly why a leak-only check
> is not enough: it would call a crashing route *isolated*.
>
>     asked     did another tenant's data come back
>     mattered  did the query ask for another tenant's data at all
>
>
> ### The refusal that handed the body back
>
> `RequestValidationError` is neither an `HTTPException` nor a domain error, so a
> 422 went out past all three handlers — carrying pydantic's `input` key, which
> on a missing field is the entire submitted body. A real drive against
> `PUT /records`:
>
>     {"type": "missing", "loc": ["body", "key"], "msg": "Field required",
>      "input": {"k": "patient-1", "v": "HIV positive, disclosed 2019"}}
>
> A record value in plaintext, on the one path in an encrypted vault that never
> touches the encryption layer.
>
> **What this is not:** disclosure between people — a 422 returns to whoever sent
> it, and here it could not happen unauthenticated at all, because the tenant
> dependency refuses before the body is validated. **What it is:** content on an
> error path, in a product whose whole design exists so that it does not travel.
>
> `type`, `loc` and `msg` are returned; `input` and `ctx` are not. The guard
> sweeps with a real tenant token on purpose: without one, twelve routes reach
> validation and forty answer 401, and the sweep would report a spotless vault it
> never asked.
>
>
> ### The synthetic self enters the tandem contract
>
> `docs/tandem.md` gains the boundary before the code that will obey it — an
> enumerated allowlist, consented per category, empty by default, with no free
> text from the user crossing at all. Byte-identical in all three repositories.

## app-v0.30.0 — PDI app-v0.30.0

- Published: 2026-08-01
- Commit: `6f5aa93e8f4e679f3111c39dbd70080eb7879083`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.30.0>

> ### The stranger's page was already right; the tenant's was not
>
> A tenant picks a language and PDI honours it: `_STRINGS` translates the
> console's chrome, `_PAGE_STRINGS` translates the recipient's server-rendered
> page against their browser's header, and the recipient's own two refusals —
> `RECEIVE_NO`, `RECEIVE_REVOKED` — are localized at the route that raises them,
> from the round that gave the recipient a door at all.
>
> The tenant's refusals were English. All sixty, on an account where the language
> picker had been answered and every other surface honoured it.
>
>     asked     is the stranger answered in their language
>     mattered  is the tenant
>
> The direction is the reverse of the usual one, and worth naming for that
> reason. Three rounds across these repositories found a stranger being served
> the language of somebody who *had* an account — the accountless screen, the
> care beacon, the objection form. Here the stranger's page was already correct
> and the account-holder's was not, because the stranger's page was built as a
> localization problem from its first line and the vault's own refusals were
> never looked at as text a person reads.
>
> **Three handlers, three shapes.** `create_app` built its responses three
> different ways: two hand-rolled `Response`s with `json.dumps`, one
> `JSONResponse`. None of that was wrong on its own, and it is exactly how a
> fourth arrives with a fourth shape and no translation — the sibling repository
> found the same drift at eight. All of them now return through `i18n.refuse`,
> and `test_every_handler_returns_through_the_one_place` reads `api.py`'s AST and
> fails the next one that does not.
>
> **Eleven** sentences translated into all nine languages: every credential and
> key check, which is what any route can raise. **49** more recorded in
> `pdi/tests/refusals_untranslated.txt` and ratcheted, with the 30 f-string
> refusals named in the header as a class the file does not cover, and the
> `PDI_ADMIN_TOKEN` message named as one that stays English by decision — its
> reader is an operator and its fix is the name of an environment variable.
>
> `tr_refusal` consults all three tables so `RECEIVE_NO` is not translated twice,
> and a test asserts it is not: two copies of one sentence are free to drift, and
> the reader who got the stale one would have no way to tell.

## app-v0.29.0 — PDI app-v0.29.0

- Published: 2026-08-01
- Commit: `94ed76b593602365899411f0874f492ed0ed5108`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.29.0>

> Aligned with QRME and JIM-mini 0.29.0. The three products carry one version,
> so a release that only moves in two of them still moves in all three.
>
> Nothing in PDI's own code changed this cut. QRME gained the cloudgw deploy
> runbook and a guard for translated strings nothing looks up; JIM localized its
> console navigation and put a number on the six hundred and seventy-seven
> English strings its gated screens carry. PDI has neither a console
> localization layer nor an unmeasured pre-session surface — its stranger-facing
> pages are server-rendered and already localized, under nineteen tests that
> have been passing since 0.24.0.

## app-v0.28.0 — PDI app-v0.28.0

- Published: 2026-08-01
- Commit: `a35e4823e89fe296c5802f3923e071e0c6d87d0f`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.28.0>

> Aligned with JIM-mini 0.28.0. The three products carry one version, so a
> release that only moves in one of them still moves in all three.
>
> Nothing in this product's own code changed this cut. JIM's console gained the
> localization layer whose absence was measured last release, and two of its
> guards broke on the way — both asking whether a sentence was in a screen's
> *file* when what mattered was whether the screen *says* it. Neither surface
> exists here in that form.

## app-v0.25.0 — PDI app-v0.25.0

- Published: 2026-08-01
- Commit: `330e3934e890618077958580c1d8102883a90570`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.25.0>

> Aligned with QRME 0.25.0. The three products carry one version, so a release
> that only moves in one of them still moves in all three — otherwise a support
> question about "0.25" has three different answers depending on which app is
> being asked about.
>
> Nothing in PDI's own code changed this cut. QRME's round covered the two
> outstanding console-credential tasks and the Windows Hello field test, and
> found a real defect writing each one up: a WebAuthn relying party id must be a
> domain, so the signing ceremony could never have run from a loopback origin;
> and the Apple client secret is a JWT that expires within six months with no
> warning of any kind.
>
> PDI has neither surface. Recorded here so the version's contents are legible
> from this repo without opening another one.

## app-v0.21.0 — PDI app-v0.21.0

- Published: 2026-08-01
- Commit: `4017818f62df22957f626a0d2da8cbe8d9f16b15`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.21.0>

> **PDI v0.21.0 — cut in step with QRME.**
>
> The three products are cut together at one version so an installed suite never
> has to reason about which piece is which release. This one carries no PDI
> feature work: the round that produced it ran in QRME, where four console doors
> were built for backend features that had none.
>
> Three of those four rounds found a defect behind the door, and the pattern is
> worth naming here because the same door audit runs in this repository:
>
> * a room's transcript and its `advance` route asked for **no credential at
>   all**, while the microphone disclosure two routes away checked membership;
> * a delegation policy was publishable and impossible to take up, with every
>   backend rule already correct;
> * `verify_package` reported **the signature is invalid** for a package that
>   was merely missing a field, when the cryptography had verified — the reason
>   given as a bare `KeyError` repr.
>
> In each case the argument against the defect was already written down
> somewhere else in the same repository. That is the whole return on building
> the door: it puts you in front of the thing the door leads to.
>
> ## The console backlog here
>
> PDI's own per-client audit still records **84 routes** the console cannot
> reach on its own, against a union backlog that looks much smaller because the
> iOS, Android and Windows shells can reach them. That number is the honest one
> and it is unchanged this release — the ratchet holds it from rising.
>
> ## What changed
>
> Version strings only, plus the release-title convention recorded in
> `docs/releasing.md`: release titles now carry the product name, so
> `PDI app-v0.21.0` rather than a bare tag.
>
>
> ## What's Changed
> * Record what breaks on the phone and the desktop shell too by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/140
> * Cut 0.20.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/141
> * The installer could not report, and nothing said so by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/142
> * Ask each client the door question separately by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/143
> * Cut 0.20.1 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/144
> * The release title carries the product name by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/145
> * Cut 0.21.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/146
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.20.0...app-v0.21.0

## app-v0.20.0 — PDI app-v0.20.0

- Published: 2026-08-01
- Commit: `3de9db494fb4877e884791dde8feeeda6b4e7d78`
- Assets: 0
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.20.0>

> **PDI v0.20.0 — the native shells record what breaks, and the route guard
> stopped inventing work.**
>
> ## Failures from the phone and the desktop shell
>
> The consoles have recorded failures content-free since 0.19.0 — the operation
> and the status, never the message, never the path as it was typed. That is the
> governing constraint: a crash report is worth having only if nothing private
> travels in it, and the safest way to guarantee that is to have nothing private
> to send.
>
> The web console has done it since 0.19.0; **iOS, Android and the desktop shell
> had not**, so a failure that happened only on a phone happened only in silence.
> All three now record on the same terms and post to the same gateway.
>
> `docs/cloud-model.md` — byte-identical across the three repositories — gains
> the gateway's container deploy path. The gateway lives in QRME's tree, but
> every product's console posts to it, so the instructions belong wherever
> somebody is reading about the contract.
>
> ## A guard that invented work
>
> Every earlier defect in `clientpaths.py` made it too **lenient**: a truncated
> path, a verb read off a neighbouring call, a route table read flat instead of
> recursed. Those are the failures you expect from a checker.
>
> This one was the other kind. A template literal may nest another inside an
> interpolation, and the extraction pattern's backtick alternative stopped at the
> *inner* opening backtick — so a call normalised to a path no route matches, and
> a route with a working door was reported as having none.
>
> Nothing failed. The suite stayed green. The route sat on the backlog looking
> like work, and a door-building round was aimed at it before anybody noticed the
> door was already there. **A checker that invents work fails more quietly than
> one that misses some:** a miss is found by the bug it let through, while an
> invention is found only by somebody going to do the work and finding it done.
>
> Interpolations are now matched by counting braces, so a nested one passes
> through intact.

## app-v0.24.0 — PDI app-v0.24.0

- Published: 2026-08-01
- Commit: `74a51316eaefc12180c8038736efc4431129ffbf`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.24.0>

> Three rounds, one question: **when a stranger does reach the page built for
> them, can they read what it says — and does the route behind it keep the
> promise the page makes?**
>
> ## The page was not an oracle; the route it fronts was
>
> There is a test named for this. It asserts that `GET /r/{tid}` never 404s, so
> the page cannot be used to ask whether a transfer id is real. True, worth
> keeping, and not where an id gets probed.
>
> `POST /transfers/{tid}/receive` takes **no credential of any kind** — that is
> the design, the token in the header is the authorization — and it answered
> 404 `transfer not found` for an id that does not exist and 403 `invalid
> receive token` for one that does. Driven with no credential: a real id
> answers 403, an invented one answers 404. Anybody with a shell could walk ids
> and learn which sealed transfers exist, which for compliance-grade material
> is a disclosure before anything is opened.
>
> Both now answer identically, with one sentence that is true either way.
> Revoked stays distinguishable because `transfers.receive` matches the token
> hash before it looks at status, so 410 is unreachable without the real token
> — and somebody whose file was withdrawn should be told that rather than left
> with a refusal that reads like their own mistake.
>
> ## Four pages for people who are not tenants, in one language
>
> Every localization path in this vault takes a `tenant_id`. PDI serves four
> pages to people who never will be one: a courier at a sealed carrier,
> somebody at a facility gate, whoever scans a code that resolves to nothing,
> and the recipient of a sealed transfer — whom `receive_transfer` itself
> describes as holding *"no tenant credential"*. All four were English,
> whatever the reader's browser said.
>
> `negotiate()`, forty-five page strings in ten languages, and `lang`/`dir` on
> every page. A table of their own, because `localize` walks whole JSON
> responses swapping any string it recognises — safe for a long compliance
> note, not safe for the short words a page is made of. The holder line is a
> whole-sentence template filled after translation, never a translated half
> joined to a name. Card values stay verbatim: on a custody card an invented
> fact is the whole problem.
>
> ## A comment that was wrong about its own gap
>
> A note left on the found/ring script said the server's `note` and `detail`
> *"come back through the response middleware, which is the tenant's language
> rather than the reader's"*, and used that to justify preferring them over the
> page's own strings — a real question, decided.
>
> It was not a decision. The middleware keys on the *calling* tenant and these
> calls have none. Those sentences were never localized into anything, by
> anyone, in any deployment. Six of them, all read after a button rather than
> on the page: the custody receipt, the decline on a repeat report, both
> wrong-sticker mistakes, the dead code, and:
>
> > I couldn't reach anyone just now, so please don't wait on somebody coming
> > out. If there's a number on the door, call it.
>
> That last one decides whether somebody stands outside a facility in the dark
> waiting for nobody, and it was English for every caller in every country. The
> agent's own words are left alone — that is what the facility chose to say, in
> the voice its operator configured.
>
> The recipient's three sentences went the same way: the refusal, the
> revocation and the custody line on success. None of them is on a page, so the
> page checks could not see them.
>
> ## One header, three products
>
> QRME, JIM-mini and PDI each grew a `negotiate()` in a different round.
> Compared side by side for the first time, two rows disagreed. A conformance
> table now lives byte-identically in all three repositories, written as
> decisions rather than observations.
>
> ## Also
>
> - Every sentence on these pages now goes through the same escaping the card's
>   tenant data always did, so an apostrophe ships as an entity. One test read
>   the markup for it; it asks what a person reads instead.
>
> **414 tests passing.**

## app-v0.23.0 — PDI app-v0.23.0

- Published: 2026-08-01
- Commit: `be67e5a603607cf39480e6b178dd225770511e79`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.23.0>

> **PDI v0.22.0 — the console backlog reaches zero, and closes the audit across all three products.**
>
> The desktop console could not reach **84** of the vault's routes. Every one was
> present on a phone shell.
>
> | | at the start of this release | now |
> |---|---|---|
> | Console-doorless routes | 84 | **0** |
> | Routes no client anywhere calls | 3 | **0** |
> | `api.ts` bindings nothing calls | 3 | **0** |
>
> All three record files are now **empty rather than short**, and the tests that
> read them assert emptiness.
>
> ## Five new screens
>
> Screens 48–52, one per family:
>
> - **Carriers** — a sealed thing, and the code on the outside of it. The scan
>   side takes no credential at all, deliberately: a code on a crate is for
>   whoever is holding the crate. What they learn is capped by `disclose`, what
>   they can do is leave a note in the chain of custody, and `contents` is null
>   on every card. The card says it in its own words — *this code proves custody,
>   not contents*.
> - **Exchange** — what leaves sealed and what is asked to come in, with the
>   chain of custody and the audit-chain verification above it rather than under
>   it. A custody list nobody can check is a list of claims.
> - **Custody** — the key, the hardware, the paperwork. The question at the top is
>   the only one this product really answers: *can the operator decrypt this?*
>   Everything below it is downstream of the answer.
> - **Bridges** — what reaches in: a connected account, a robot on a floor,
>   another product's contributions. The contributions listing is a count and a
>   set of keys and never contents.
> - **Guiding** — the console's own guide, its corner pane, and the words it uses.
>
> Each with a walkthrough lesson and assistant phrasing.
>
> ## What driving the routes found
>
> Nothing in the vault was broken. Six places where the route table and the wire
> disagree, every one of which would have shipped as a dead button:
>
> - **`receive` and `submit` take tokens of their own, in headers of their own**
>   — `x-receive-token` and `x-submit-token`, not the tenant's bearer token. The
>   party receiving a transfer is a clinic and the party submitting to an intake
>   is a records office; neither is the tenant, has a tenant credential, or
>   should. Bound as bearer credentials both are a 403 every time.
> - **The scan page is HTML and two `qr.svg` routes are SVG.** PDI's client runs
>   `JSON.parse` on every body without guarding it, so binding them through it
>   did not return the wrong thing — it threw `SyntaxError: Unexpected token <`
>   from inside the client, which names nothing.
> - **A key provider is `held` or `kms`** — not `customer`, which is what the
>   concept is called in the plan copy, in the hosting guarantees, and in the
>   field `customer_managed` two lines from the one that rejects it.
> - **A beacon's `disclose` is a single value**, `blind` or `contact`, not the
>   list of fields to reveal that the name suggests.
> - **`ref_kind` and a ring's `kind` are four values each**, and a token's role is
>   `read` or `write`.
>
> Three of those the server answers with the exact set of legal values in its
> 422 body, so the unions in the client are transcribed from the vault rather
> than invented.
>
> ## Three things the console never offered
>
> - **What an audit action means, on the screen that lists it.** The backend has
>   published the action glossary since the log existed; the console showed raw
>   action names beside it. A log whose vocabulary is undocumented where it is
>   read is a log somebody has to guess at during an incident.
> - **Whether a page could have been delivered at all.** The gateway listed pages
>   and whether each arrived, and never said whether a channel was configured —
>   so a deployment with none showed *nothing paged*, which reads as a quiet week
>   and means the opposite.
> - **Revoking a grant token.** Revoking a bequest and killing the token it has
>   already handed to a person are different acts. Only the softer one had a
>   button.
>
> ## The audit could not see three of its own new doors
>
> Adding the text helper made the scan page and both `qr.svg` routes invisible to
> `clientpaths`, which reads one shape of call — it reported them as newly
> doorless in the same commit that gave them working buttons. That is the third
> extractor false positive here, after the nested template and the `<img src>`,
> and the lesson has not changed.
>
> ## Two guards that could only pass while the problem existed
>
> One asserted the union backlog was *strictly* smaller than the console's; the
> other asserted the snapshot file was non-empty. A check that can only be
> satisfied by the problem still existing is not a check. Both rewritten.
>
> **Suite: 359 passing, 1 skipped.**
>
> ---
>
> Cut in step with [QRME](https://github.com/davidsbianchi1984/qrme) and
> [JIM-mini](https://github.com/davidsbianchi1984/jim-mini), both also at
> v0.22.0. All three reached zero on the same audit in this release.

## app-v0.22.0 — PDI app-v0.22.0

- Published: 2026-07-31
- Commit: `039e41edab9d7ecc1cbe2f5d1e1f488f69faaae9`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.22.0>

> **PDI v0.22.0 — the console backlog reaches zero, and closes the audit across all three products.**
>
> The desktop console could not reach **84** of the vault's routes. Every one was
> present on a phone shell.
>
> | | at the start of this release | now |
> |---|---|---|
> | Console-doorless routes | 84 | **0** |
> | Routes no client anywhere calls | 3 | **0** |
> | `api.ts` bindings nothing calls | 3 | **0** |
>
> All three record files are now **empty rather than short**, and the tests that
> read them assert emptiness.
>
> ## Five new screens
>
> Screens 48–52, one per family:
>
> - **Carriers** — a sealed thing, and the code on the outside of it. The scan
>   side takes no credential at all, deliberately: a code on a crate is for
>   whoever is holding the crate. What they learn is capped by `disclose`, what
>   they can do is leave a note in the chain of custody, and `contents` is null
>   on every card. The card says it in its own words — *this code proves custody,
>   not contents*.
> - **Exchange** — what leaves sealed and what is asked to come in, with the
>   chain of custody and the audit-chain verification above it rather than under
>   it. A custody list nobody can check is a list of claims.
> - **Custody** — the key, the hardware, the paperwork. The question at the top is
>   the only one this product really answers: *can the operator decrypt this?*
>   Everything below it is downstream of the answer.
> - **Bridges** — what reaches in: a connected account, a robot on a floor,
>   another product's contributions. The contributions listing is a count and a
>   set of keys and never contents.
> - **Guiding** — the console's own guide, its corner pane, and the words it uses.
>
> Each with a walkthrough lesson and assistant phrasing.
>
> ## What driving the routes found
>
> Nothing in the vault was broken. Six places where the route table and the wire
> disagree, every one of which would have shipped as a dead button:
>
> - **`receive` and `submit` take tokens of their own, in headers of their own**
>   — `x-receive-token` and `x-submit-token`, not the tenant's bearer token. The
>   party receiving a transfer is a clinic and the party submitting to an intake
>   is a records office; neither is the tenant, has a tenant credential, or
>   should. Bound as bearer credentials both are a 403 every time.
> - **The scan page is HTML and two `qr.svg` routes are SVG.** PDI's client runs
>   `JSON.parse` on every body without guarding it, so binding them through it
>   did not return the wrong thing — it threw `SyntaxError: Unexpected token <`
>   from inside the client, which names nothing.
> - **A key provider is `held` or `kms`** — not `customer`, which is what the
>   concept is called in the plan copy, in the hosting guarantees, and in the
>   field `customer_managed` two lines from the one that rejects it.
> - **A beacon's `disclose` is a single value**, `blind` or `contact`, not the
>   list of fields to reveal that the name suggests.
> - **`ref_kind` and a ring's `kind` are four values each**, and a token's role is
>   `read` or `write`.
>
> Three of those the server answers with the exact set of legal values in its
> 422 body, so the unions in the client are transcribed from the vault rather
> than invented.
>
> ## Three things the console never offered
>
> - **What an audit action means, on the screen that lists it.** The backend has
>   published the action glossary since the log existed; the console showed raw
>   action names beside it. A log whose vocabulary is undocumented where it is
>   read is a log somebody has to guess at during an incident.
> - **Whether a page could have been delivered at all.** The gateway listed pages
>   and whether each arrived, and never said whether a channel was configured —
>   so a deployment with none showed *nothing paged*, which reads as a quiet week
>   and means the opposite.
> - **Revoking a grant token.** Revoking a bequest and killing the token it has
>   already handed to a person are different acts. Only the softer one had a
>   button.
>
> ## The audit could not see three of its own new doors
>
> Adding the text helper made the scan page and both `qr.svg` routes invisible to
> `clientpaths`, which reads one shape of call — it reported them as newly
> doorless in the same commit that gave them working buttons. That is the third
> extractor false positive here, after the nested template and the `<img src>`,
> and the lesson has not changed.
>
> ## Two guards that could only pass while the problem existed
>
> One asserted the union backlog was *strictly* smaller than the console's; the
> other asserted the snapshot file was non-empty. A check that can only be
> satisfied by the problem still existing is not a check. Both rewritten.
>
> **Suite: 359 passing, 1 skipped.**
>
> ---
>
> Cut in step with [QRME](https://github.com/davidsbianchi1984/qrme) and
> [JIM-mini](https://github.com/davidsbianchi1984/jim-mini), both also at
> v0.22.0. All three reached zero on the same audit in this release.
>
>
> ## What's Changed
> * The release title carries the product name by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/145
> * Cut 0.21.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/146
> * PDI console doors: the 84-route backlog reaches zero by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/147
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.20.1...app-v0.22.0

## app-v0.20.1 — PDI app-v0.20.1

- Published: 2026-07-31
- Commit: `2b849d574f2fd61093da137393d4eeb69204a65d`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.20.1>

> **PDI v0.20.1 — the union hid a surface.**
>
> `clientpaths.doorless` unions the console with the iOS, Android and Windows
> shells, so a route only the phone calls counts as doored. The union backlog
> reads **58**; the console alone cannot reach **84 routes**. The guard
> was answering *some client can reach this*, which was true, in place of *this
> client can reach this*, which was not.
>
> That is the shape of every defect this audit has produced: a checker answering
> a question slightly to the left of the one that matters, and passing. In QRME
> the gap turned out to be the entire seller's side of the product — post a
> licence offer, see who holds one, revoke it, read what it earned, ask to be
> paid — all present on the phone, all absent from the desk.
>
> ## Two new guards
>
> - **`test_the_console_is_a_client_too.py`** — the console's own backlog, in
>   `console_doorless.txt`, checked in both directions and ratcheted so it cannot
>   grow past where it started. The union guard stays; a route no client anywhere
>   calls is still worse. A phone-only capability is a legitimate design choice,
>   which is what the snapshot is for: deferring one takes a deliberate edit and
>   shows up in a diff.
> - **`test_a_binding_is_not_a_door.py`** — the same mistake one level down. A
>   function in `api.ts` that no screen calls is not a door, and `doorless`
>   counted it as one. The docstring on `doorless` had said this was *"a
>   discipline rather than something the test can enforce"*; it is enforceable in
>   about twenty lines. *The test cannot check this* is a claim worth testing.
>   This repository has **three**.
>
> ## Fixed
>
> - **`clientpaths.py` was not byte-identical across the three repositories**,
>   though it says it is. This copy never received the `fetch`, `window.open`,
>   `<img src>` and `<a href>` call forms from 0.20.0, so its backlog counted
>   doors that already existed. Restored.
> - **The pairing QR is built from a literal.** `Settings.tsx` rendered it as
>   `getBase() + pair.qr_svg`, where the path arrives in a response body — a real
>   door no static check can see. `GET /pair/qr.svg` sat in `NOT_A_CLIENT_CALL`
>   for exactly that reason, which is an exemption made out of a blind spot; the
>   last one of those turned out to have no door at all. Same request, now
>   visible to the audit.
>
> ## Cut together
>
> QRME, JIM-mini and PDI move on one version number. QRME's 0.20.1 additionally
> carries the seller's-side console screen and three money defects the building
> of it exposed — including a marketplace sale credited to a profile id while the
> statement reads by account id. See [QRME's notes](https://github.com/davidsbianchi1984/qrme/blob/main/RELEASE_NOTES.md).
>
>
> ## What's Changed
> * Stop the route guard inventing work by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/139
> * Record what breaks on the phone and the desktop shell too by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/140
> * Cut 0.20.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/141
> * The installer could not report, and nothing said so by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/142
> * Ask each client the door question separately by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/143
> * Cut 0.20.1 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/144
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.19.1...app-v0.20.1

## app-v0.19.1 — app-v0.19.1

- Published: 2026-07-30
- Commit: `2d86a855b06834769586a945f46bc84b1fd97e80`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.19.1>

> **PDI v0.19.1** — a feature can no longer ship with nothing drawn.
>
> The gallery tests all check screens against the README: a reference with no
> file, a file with no reference, a gap in the numbering. Every one of them
> starts from the screens. **None asked the opposite question — does this surface
> have a screen at all?** So a feature could ship undrawn, untaught and
> unreachable from the in-app helper, and the suite stayed green.
>
> That had happened three times, most recently to 0.19.0's own error-reporting
> card and its first-run notice, which went out undrawn while the release notes
> described them at length. It is the same shape of flaw found twice before here:
> a guard that only walks the relation in the direction where the answers already
> exist.
>
> `ui_screens.txt` is the missing direction. Every console surface carries a
> screen number, `undrawn`, or `unaudited`, so a surface nobody has classified
> fails in the round that introduces it. The mapping is declared rather than
> guessed — matching component names to screen titles resolved only a fraction of
> them, because titles are written for the person using the app and component
> names for the person editing it.
>
> Both backlogs are ratcheted against a ceiling each repository declares for
> itself, and a ceiling left high after the backlog falls fails too: a ratchet
> that stops ratcheting re-opens the ground it gained. Five failures were injected
> to prove it bites, including the one that matters — silencing the check by
> writing `undrawn` fails the ratchet.
>
> **And the two surfaces it caught are drawn.** Screens **46 What Went Wrong** and **47 Before Anything Is Sent** join the gallery, each
> with a lesson and with phrasings that reach it in the words somebody actually
> types when something has broken: "it failed", "something broke", "stop
> sending", "opt out". The card draws an operation and a status and nothing else,
> because that is all the log holds.
>
> **No application behaviour changes in this release** — screens, gallery,
> lessons, helper phrasings, and the guard that will keep them honest.
>
>
> ## What's Changed
> * Fail when a surface ships with no drawing, then draw the two that did by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/137
> * Cut 0.19.1 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/138
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.19.0...app-v0.19.1

## app-v0.19.0 — app-v0.19.0

- Published: 2026-07-30
- Commit: `675b8cf49994f09e2f60b48df20f5f336b4c65f7`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.19.0>

> **PDI v0.19.0** — the console can tell you what broke, without telling you
> anything about anybody.
>
> Every failed request is now recorded and, where a build has somewhere to
> send, reported. What gets kept is the *operation* and the status code:
> `POST /bequests/{id}/activate → 500` identifies a bug, where the
> unredacted version of that path identifies a person and an arrangement
> they made. Only the first is written down, and the redaction happens
> before the row is stored, so there is no moment at which the buffer holds
> something that would later have to be scrubbed. A query string can name a
> vault key; it never survives.
>
> **Nothing goes before you have been asked.** Sending is opt-out, which
> only means something if the opting-out can happen before the first report
> rather than being discovered afterwards in a panel nobody opened. A
> first-run notice holds everything until it is answered — and it shows the
> actual payload rather than describing it, from the same function that
> sends it, so it cannot go stale while still reading honestly. The switch
> in Settings is that same answer, changeable whenever.
>
> Counts are sent as **deltas**: each row remembers how much of itself has
> been reported, so reopening the app twenty times does not turn one broken
> screen into twenty. A failed send moves nothing, and the next launch
> retries.
>
> **The receiving gateway refuses rather than redacts.** It accepts exactly
> five top-level keys and five per problem and rejects anything else — an
> unknown field, a `platform` string long enough to hide a sentence, a `day`
> carrying a time of day, a path with an unredacted id still in it. It could
> redact that path itself; doing so would let a build whose redaction had
> broken keep working while nobody learned that every report from those
> users had been arriving with an id in it.
>
> **Nothing here touches the vault.** No record, no key and no seal is
> involved — the log holds route shapes and status codes, and the vault's
> own contract is unchanged. Nothing in this release alters what a key
> opens.
>
> **Off by default, by absence rather than by flag.** The collector address
> is compiled in at build time and unset, so an installer built without one
> has nowhere to send and no code path that could acquire one. There is no
> address for a later mistake to switch on.
>
> **Fixed** — four bugs found by running the thing rather than reasoning
> about it. The gateway had no CORS at all, so every browser preflight would
> have been refused and every report would have failed silently. Its
> validators were anchored with `$`, which in Python also matches before a
> trailing newline, so `Win32\n` passed a check whose error message promised
> newlines were not allowed. A counter file that was valid JSON of the wrong
> shape was adopted wholesale and took the read endpoint down with it. And
> the test guarding the payload shape ran only in the repository that ships
> the gateway, not here.
>
>
> ## What's Changed
> * Check PDI's four client surfaces against its own route table by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/128
> * Check the verb, not just the address by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/129
> * Every option the vault offers, it now has to accept by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/130
> * Ask the inverse question: which routes have no door? by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/131
> * Continuity finally has a door by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/132
> * Exclude a desk's view and beacon QR from the doorless audit by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/133
> * Record what fails, without recording anything private by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/134
> * Send the error reports, and refuse anything that is not one by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/135
> * Cut 0.19.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/136
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.18.0...app-v0.19.0

## app-v0.18.0 — PDI app-v0.18.0

- Published: 2026-07-30
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.18.0>

> **PDI v0.18.0** — cut with the siblings.
>
> **No functional changes here**: cut with the siblings so the suite carries
> one version.
>
> JIM-mini and QRME both finished something they had each claimed twice and
> completed neither: every feature with a door in their web consoles now has
> one in the iOS, Android and Windows shells. JIM gained the guidance
> effectiveness loop, the adaptation profile and the anonymity posture
> natively; QRME gained provenance lookup and the advisor/collaborator/
> operator role. Seven screens were drawn, seven lessons written, and every
> one made reachable by asking the in-app helper in ordinary words — a
> convention both repos had quietly stopped following for two versions.
>
> The vault's own contract is unchanged: what JIM seals here stays sealed
> here, and nothing in this release alters what a key opens.
>
>
> ## What's Changed
> * The 0.14.5 link points at the cut commit, not a tag that never shipped by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/123
> * Cut 0.16.0, and cite both publication numbers by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/124
> * The closing passage is not a release note by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/125
> * Cut 0.17.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/126
> * Cut 0.18.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/127
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.15.0...app-v0.18.0

## app-v0.15.0 — app-v0.15.0

- Published: 2026-07-29
- Commit: `7a1cf6e7c6484a5ccad4858432d92bd5f9b2a106`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.15.0>

> **PDI v0.15.0** — **no functional change in this release**: cut with
> the siblings. JIM-mini gained guided wellness (calm protocols,
> workout plans, meal plans, a nutrition Coach area and the Wellness
> tab) and QRME gained the temperament dial group.
>
> ### Verification
>
> Full suite green.
>
> ### Install
>
> If you have 0.7.0 or later, this arrives on its own — one restart when
> prompted.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.14.5 — cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/121
> * Cut 0.15.0 — cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/122
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.14.4...app-v0.15.0

## app-v0.14.4 — PDI app-v0.14.4

- Published: 2026-07-29
- Commit: `48da39cfe75bd4988f67049509719b2c2620f079`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.14.4>

> **PDI v0.14.4** — the console names a version mismatch.
>
> The same guard as the siblings: the console compares its build
> version with /health's on launch and, on mismatch, shows a banner
> naming both versions and the address — with a one-click "use this
> app's own backend" when a stored address is the culprit.
>
> ### Verification
>
> Full suite green.
>
> ### Install
>
> If you have 0.7.0 or later, this arrives on its own — one restart when
> prompted.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * The console names a version mismatch by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/119
> * Cut 0.14.4 — the console names a version mismatch by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/120
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.14.3...app-v0.14.4

## app-v0.14.3 — app-v0.14.3

- Published: 2026-07-29
- Commit: `d3e0cc54a16b497a0b4334cf750d6cc83e11aad6`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.14.3>

> JIM-mini v0.14.3 — a documentation binding pass.
> Every README in the repo (app and the native shells) is now held to the same closing convention, byte-identical, enforced by a binding test so the next README added cannot drift.
> Verification
> Full suite green.
> Install
> If you have 0.7.0 or later, this arrives on its own — one restart when prompted.
> Full changelog: https://github.com/davidsbianchi1984/jim-mini/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.9.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/101
> * Cut 0.9.1 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/102
> * Cut 0.10.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/103
> * Cut 0.11.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/104
> * The desktop app finally carries its own vault — 0.11.1 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/105
> * Cut 0.12.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/106
> * The operations journal: sealed coordination records, readable in place by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/107
> * The console shows the operations journal by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/108
> * Cut 0.13.0 — the operations journal by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/109
> * Docs round: the tandem contract + invention disclosure catch up by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/110
> * Cut 0.13.1 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/111
> * Operations entries prove themselves by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/112
> * Cut 0.14.0 — operations entries prove themselves by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/113
> * Cut 0.14.1 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/114
> * Docs: suite mode enters the tandem contract by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/115
> * Cut 0.14.2 — cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/116
> * Every README ends on the rock by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/117
> * Cut 0.14.3 — every README ends on the rock by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/118
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.8.0...app-v0.14.3

## app-v0.8.0 — PDI v0.8.0

- Published: 2026-07-29
- Commit: `main`
- Assets: 8
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.8.0>

> **PDI v0.8.0** — the continuity round: the vault learns what happens when
> you are gone. One of three interoperating products, all three cut
> together at this version.
>
> ### Bequests
>
> The vault's whole posture is *nobody but you* — your hardware, your keys,
> your walls. Locked perfectly is also locked away from the daughter
> settling the estate or the doctor treating what the deceased knew and she
> didn't. A **bequest** is the owner's answer, written while they are fine:
> *this person* may read *these scopes* when *this condition* is attested.
>
> - **No credential exists until activation.** A bequest at rest holds a
>   name and a list of key prefixes — no token, nothing a database breach
>   or a curious operator could hand a grantee early. The grant token is
>   minted at activation, shown once; only its hash survives.
> - **Activation requires an attestation** — a JIM-mini vigil event id, a
>   QRME succession verification, a death-certificate number — recorded in
>   the tamper-evident audit chain. The attestation trail is the product.
> - **The grant reads its shelf and nothing else, forever.** Every read is
>   audited. The owner can revoke while alive; the admin after activation.
>   A customer-held key (BYOK) remains part of the estate — the grantee
>   presents it or reads nothing.
>
> ### Verification
>
> 266 tests green, including that a bequest at rest holds no credential,
> that activation without a reference is refused, that the grant cannot
> read outside its scopes, that a revoked grant and a wrong token look
> alike, and that every step lands in the audit chain with the attestation
> reference on it.
>
> ### Install
>
> If you have 0.7.0, this arrives on its own — one restart when prompted.
> Otherwise, download the installer for your OS from the assets below, or
> run `python -m pdi`. Deployed on-premises or in colocation — your
> hardware, your keys (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * The app keeps itself current, and the window says PDI — 0.7.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/99
> * Bequests: vault access that begins only at attestation — 0.8.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/100
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.6.1...app-v0.8.0

## app-v0.6.1 — PDI v0.6.1

- Published: 2026-07-29
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.6.1>

> **PDI v0.6.1** — **no functional change to the vault in this release**: no
> new routes, no schema, no behaviour. One of three interoperating products
> (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> The model layer became honest about degrades: JIM-mini's coach no longer
> answers chat with crisis-flavored fallback text, every reply names the
> provider that actually produced it (with an amber warning and the reason
> on a degrade), and both consoles' settings say plainly when the built-in
> offline helper is what will answer.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.6.1` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.5.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/94
> * Cut 0.6.0 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/95
> * Cut 0.6.1 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/96
> * Make the license say one thing, and record the inventions with dates by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/97
> * Restore the owner's LICENSE exactly as he wrote it by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/98
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.8...app-v0.6.1

## app-v0.4.8 — PDI v0.4.8

- Published: 2026-07-29
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.8>

> **PDI v0.4.8** — **no functional change to the vault in this release**: no
> new routes, no schema, no behaviour. One of three interoperating products
> (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> Verification matches the deployment: desktop installs (no mail transport)
> activate accounts directly; SMTP deployments email a clickable verify link
> (code as fallback) and the apps continue on their own after the click.
> Crashed signups no longer strand the retry.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.8` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.4.7 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/92
> * Cut 0.4.8 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/93
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.6...app-v0.4.8

## app-v0.4.6 — PDI v0.4.6

- Published: 2026-07-28
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.6>

> **PDI v0.4.6** — **no functional change to the vault in this release**: no
> new routes, no schema, no behaviour. One of three interoperating products
> (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> Verification matches the deployment: desktop installs (no mail transport)
> activate accounts directly; SMTP deployments email a clickable verify link
> (code as fallback) and the apps continue on their own after the click.
> Crashed signups no longer strand the retry.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.6` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.4.6 — no functional change; cut with the siblings by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/91
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.5...app-v0.4.6

## app-v0.4.5 — PDI v0.4.5

- Published: 2026-07-28
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.5>

> **PDI v0.4.5** — **no functional change to the vault in this release**: no
> new routes, no schema, no behaviour. One of three interoperating products
> (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> Verification matches the deployment: desktop installs (no mail transport)
> activate accounts directly; SMTP deployments email a clickable verify link
> (code as fallback) and the apps continue on their own after the click.
> Crashed signups no longer strand the retry.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.5` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.4.5 — no functional change; the siblings' verification matched the deployment by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/90
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.4...app-v0.4.5

## app-v0.4.4 — PDI v0.4.4

- Published: 2026-07-28
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.4>

> **PDI v0.4.4** — **no functional change to the vault in this release**: no
> new routes, no schema, no behaviour. One of three interoperating products
> (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> The Windows signup 500 died: the emailed-code banner used characters the
> frozen Windows backend's console encoding cannot print, so every signup
> crashed mid-request. ASCII banner, replace-don't-raise stdout, a cp1252
> guard test, and consoles that show a server's actual words instead of a
> JSON-parse exception.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.4` tag), or run
> `python -m pdi`. Deployed on-premises or in colocation — your hardware,
> your keys (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Cut 0.4.4 — no functional change; the siblings' Windows signup 500 died by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/89
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.3...app-v0.4.4

## app-v0.4.3 — PDI v0.4.3

- Published: 2026-07-28
- Commit: `d364493ff5863bf28df85b5492ccef4add706435`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.3>

> **PDI v0.4.3** — **no functional change to the vault in this release**: no new
> routes, no schema, no behaviour. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### What changed in the siblings
>
> QRME and JIM-mini gained a **front door and a key of your own**: email +
> password accounts with the address proven by a 6-digit emailed code before
> sign-in works, password reset that revokes every session, no endpoint that
> reveals who has an account; **bring-your-own model key** riding each request
> and never stored server-side; and installers that ship the whole Python
> backend **frozen inside them** and spawn it at launch — double-click-and-
> done. Nothing on those paths touches PDI: account passwords and codes are
> hashed in the siblings' own stores, and the model keys never persist
> anywhere.
>
> ### Verification
>
> 256 tests green, unchanged in behaviour — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.3` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * The desktop installers were labelled 0.3.3 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/86
> * Cut 0.4.2 — no functional change; the installers are named for it by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/87
> * Cut 0.4.3 — no functional change; the siblings got the front door by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/88
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.1...app-v0.4.3

## app-v0.4.1 — PDI v0.4.1

- Published: 2026-07-28
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.1>

> **PDI v0.4.1** — **no functional change to the vault in this release**: no new
> routes, no schema, no behaviour. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> ### The vault promise says which plans it covers
>
> QRME and JIM-mini gained free tiers whose storage posture is an **open
> cloud** under platform custody: the apps hold that data themselves, over
> ordinary HTTPS, and it **never reaches PDI at all**. Two claims on this side
> were written when a paid plan was the only kind, and read as more than they
> are:
>
> - *"The tandem is the only place JIM-mini and QRME may put sensitive
>   material"* — true on a paid plan, and the hosting page now says so, naming
>   what the free posture is instead (including the short list each product
>   refuses to store open, rather than leaving a reader to assume there is
>   none).
> - *"No raw user data ever leaves your vault"* — that is about what is
>   inside, and PDI holds what the integrating apps *send* it. The free plans
>   send nothing here. The promise now scopes itself.
>
> Nothing PDI holds is less protected because somebody else is on a free plan.
> **A vault has one posture**, `hosting.GUARANTEES` is still one list shared by
> all four hosting modes, and a test still asserts no mode can hold fewer.
>
> ### Verification
>
> 255 tests green, unchanged — which is the point.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.4.1` tag), or run `python -m pdi`.
> Deployed on-premises or in colocation — your hardware, your keys
> (`PDI_MASTER_KEY`), your walls.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Name screen files in one place here too by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/83
> * Say which plans the vault promise is about by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/84
> * Cut 0.4.1 — the vault promise says which plans it covers by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/85
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.4.0...app-v0.4.1

## app-v0.4.0 — PDI app-v0.4.0

- Published: 2026-07-27
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.4.0>

> **PDI v0.3.3** — **no functional change to the vault in this release**: no new
> routes, no schema, no behaviour. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version, so one number names one combination of all three.
>
> The round belongs to the console.
>
> ### The agent status light, where amber means someone is at a door
>
> Green *working*, amber *needs you*, red *stopped*. On most surfaces amber is an
> abstraction; here it is a person standing outside, waiting to be let in.
>
> Screen 38 showed one gate agent, and nothing showed all of them — which on a
> site with a dozen entrances is the wrong shape. **Screen 39** groups them by
> light, so the amber group is the row a thumb lands on without aiming.
>
> **The overlay** rides over an ordinary view and over **every** desktop view. A
> console is watched from, not visited, and leaving an amber gate agent sitting
> on a screen nobody is looking at is the worst version of the problem this
> exists to solve. It is shaped like the watch face rather than as a bar across
> the screen: a small translucent box in the corner, three stacked rows, each its
> own tap target.
>
> The mapping lives once, in QRME's `agentlight.py`, for all three products.
>
> ### The README leads with the console screens now
>
> Everything you can look at is above everything you have to read, and the
> run / config / API material is gathered under one **Reference** heading at the
> bottom — so a command spotted in a screenshot has one place to go and look it
> up. Those tables are set smaller, because they are for looking things up in
> rather than reading through.
>
> ### Also fixed
>
> - Screen 38 said "loading dock facility beacon", which said nothing. The rows
>   now describe what is actually happening: someone at the door, a delivery
>   directed round to goods-in, somebody who wants to be let in.
> - The README claimed 38 desktop-frame counterparts. There are 40.
>
> ### Verification
>
> 192 tests green. Console screens regenerated across all three mobile platforms
> and the desktop console for macOS and Windows.
>
> ### Install
>
> Download the installer for your OS from the assets below (built by the
> `desktop-release` workflow from the `app-v0.3.3` tag), or run `python -m pdi`.
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Agent status light on the console, and say what the gate agent is doing by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/80
> * Release 0.3.3, and a README that leads with the console screens by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/81
> * v0.4.0 — where the vault lives, the console guide, and the corner pane by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/82
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.3.2...app-v0.4.0

## app-v0.3.2 — app-v0.3.2

- Published: 2026-07-27
- Commit: `89052bf5d603ea195b931247c01a2e6bfd98972c`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.3.2>

> **PDI v0.3.2** — **no functional change to PDI in this release**: no new
> routes, no schema, no behaviour. The version moves because the three products
> are cut as one release, and a number naming one combination of three is only
> useful if it never skips one. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### What changed in the siblings
>
> **QRME's starter collection stopped looking like a directory.** Each of the 34
> profiles is now shown as the card the app actually gives it — the avatar bubble,
> the role, the rating people left, skill chips, Memory / Relationships /
> Engagement, a career, a review, and a Talk-to button — two columns wide, so a
> phone stops slicing the fourth column mid-word.
>
> And the one starter that had no source material at all now has a Field Pack of
> its own. The age wall on that profile governs who may talk to her; it had been
> quietly read as a reason for her to know less about her own subject.
>
> ### Verification
>
> 192 tests green — **the same 192, passing the same way**, which is the
> point of a release claiming no functional change. 81 routes, also
> unchanged. Version strings moved in exactly five places: `pyproject.toml`, the
> FastAPI app, `app/package.json`, and the two root entries in its lockfile
> (dependency versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Release prep v0.3.2 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/79
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.3.1...app-v0.3.2

## app-v0.3.1 — PDI app-v0.3.1

- Published: 2026-07-26
- Commit: `03185e4257b8ba9fc7a253dfb721fa0f87ff1cb0`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.3.1>

> **PDI v0.3.1** — **no functional change to PDI in this release**: no new routes,
> no schema, no behaviour. The version moves because the three products are cut as
> one release, and a number naming one combination of three is only useful if it
> never skips one. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### Changed
>
> **The README names its release, and says what each one added.** The same section
> went into all three repositories, with one difference that belongs only here:
> several rounds land in PDI as *no functional change*, and the table says so
> rather than padding them.
>
> That is worth stating plainly rather than hiding. PDI is the bottom layer, and
> when the products above it learn to handle something new, the vault's correct
> contribution is usually to hold the bytes exactly as it already did. A release
> history that invented activity for those rounds would misrepresent what this
> product is for.
>
> ### Known gap
>
> **`docs/tandem.md` is still 92 lines shorter here than in the sibling
> repositories.** That file is meant to be byte-identical across `qrme`, `jim-mini`
> and `pdi`, and the *Reaching a real clinician* section added in 0.3.0 never
> reached this one — so the vault product's own copy omits the flow that seals
> clinical notes into the vault. The gap was invisible from inside this repository,
> which is how it survived a release.
>
> The fix is written and is being held with unrelated unreleased work rather than
> split apart; it lands next round. It is recorded here rather than left silent,
> because a gap nobody wrote down is one that survives another release too.
>
> ### What changed in the siblings
>
> - **QRME** — the starter profiles stopped answering from tone alone. All 34
>   shipped with zero source material while the packs matching them sat unused in
>   the marketplace.
> - **JIM-mini** — no functional change either; the README gained a release table,
>   and four screens that shipped in 0.3.0 became findable.
>
> ### Verification
>
> 192 tests green — **the same 192, passing the same way**, which is the point of a
> release claiming no functional change. 81 routes, also unchanged. Version strings
> moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency versions
> untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Say what version this is, and what each release actually added by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/76
> * Release prep v0.4.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/77
> * Renumber this release 0.3.1, not 0.4.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/78
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.3.0...app-v0.3.1

## app-v0.3.0 — app-v0.3.0

- Published: 2026-07-26
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.3.0>

> **PDI v0.3.0** — **no functional change to PDI in this release**, but not an
> empty round either. The vault is where this round's most sensitive new payload
> lands. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version.
>
> ### What the vault now holds
>
> QRME learned to put somebody in front of a **real clinician**, and to let that
> clinician write back. The note comes here: sealed under a
> `qrme/{profile}/clinical/…` key, content in the vault with only a key reference
> held next door — the same treatment source material has always had, and PDI's
> provenance attributes it to QRME the same way.
>
> That is the whole of PDI's involvement, and it is deliberately unremarkable.
> The interesting decisions this round were about *who may release* that data and
> *how it is attributed once released*, and both belong to the products that hold
> the conversation, not to the vault that holds the bytes.
>
> ### Changed
>
> - **`docs/tandem.md`** — the shared architecture doc, byte-identical across the
>   three repos, gained two sections it did not describe: handing a specialist a
>   *task* rather than a chat turn, and reaching a real clinician with the release
>   authorised by a verified WebAuthn assertion instead of a `consent: true`
>   boolean. Both record **why the obvious implementation was rejected**, which is
>   the part worth writing down — the routes are discoverable, the reason they are
>   not the obvious ones is not.
>
> ### What changed in the siblings
>
> - **QRME** — owner-authorized workflow delegation; a medical referral signed for
>   rather than consented to, with a one-time link; the clinician's note back,
>   attributed rather than absorbed; and the README's starter gallery rendering
>   avatar bubbles instead of 34 black boxes.
> - **JIM-mini** — reaching a real clinician through the tandem without ever
>   holding the credential; handing a specialist a task that outlives the app
>   closing; and a contribution preview that finally keeps the promise the
>   settings screen was already making.
>
> ### Verification
>
> 192 tests green — **the same 192, passing the same way**, which is the point of
> a release that claims no functional change here. 81 routes, also unchanged.
> Version strings moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency
> versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Document delegated workflows in the shared tandem doc by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/74
> * Release prep v0.3.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/75
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.2.2...app-v0.3.0

## app-v0.2.2 — app-v0.2.2

- Published: 2026-07-26
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.2.2>

> **PDI v0.2.2** — a documentation release. **No code changed**: no new routes, no
> schema, no behaviour, and nothing about how the vault seals or releases
> anything. Everything here corrects something that was *described* wrongly. One
> of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version.
>
> Unlike v0.2.1 — which was an honestly empty round here, with the work next door
> — this one has entries of its own.
>
> ### Fixed
>
> - **Three releases of changelog links were missing.** `[0.1.9]`, `[0.2.0]` and
>   `[0.2.1]` had headings but no link definitions, so three shipped versions
>   rendered as literal `[0.2.1]` bracket text rather than linking to their
>   releases, and `[Unreleased]` still compared against `app-v0.1.8` —
>   presenting a three-release diff as though it were an empty one.
>
> - **The release checklist is why that kept happening**, and is the entry that
>   matters. `docs/releasing.md` step 1 said to move the `Unreleased` items under
>   the new heading and date it, and stopped — it never mentioned the link
>   definition at the bottom of the file. The step was skipped three releases
>   running by someone following the instructions correctly, and nothing
>   complains when you miss it: the heading renders fine without a definition,
>   and the damage appears hundreds of lines from where the edit was made.
>
>   Step 2 was wrong in the same direction. It named `pyproject.toml` and
>   `app/package.json` when the version string lives in **five** places — the two
>   it omitted being the `FastAPI(...)` call in `pdi/api.py` and the second root
>   entry in `app/package-lock.json`, both of which had to be rediscovered each
>   round. Both steps now say what they meant.
>
>   The `0.1.5` and `0.1.6` entries still point at commits rather than tags.
>   That is deliberate and explained in `docs/releasing.md`; they are untouched.
>
> ### What changed in the siblings
>
> - **QRME** — `POST /marketplace/seed` still advertised itself as *"Idempotent —
>   already-seeded profiles are skipped"* after v0.2.1 taught it to **repair**
>   too, so the text in the OpenAPI docs pointed away from the one call that
>   fixes a deployment showing bare initials instead of portraits. Corrected in
>   four places.
>
> - **JIM-mini** — the same checklist and changelog-link corrections as here.
>
> ### Verification
>
> 192 tests green — **the same 192, passing the same way**, which is the point of
> a release that claims no functional change. 81 routes, also unchanged. Version
> strings moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency
> versions untouched). Every version heading in the changelog was checked against
> its link definition — 12 for 12.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Fix the changelog release links and the checklist that lost them by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/72
> * Release prep v0.2.2 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/73
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.2.1...app-v0.2.2

## app-v0.2.1 — app-v0.2.1

- Published: 2026-07-26
- Commit: `5f67e50283512d6474b364841a5d0f1de503633d`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.2.1>

> **PDI v0.2.1** — **there are no functional changes to PDI in this release.** The
> three products version as one, and this round's work was next door. One of three
> interoperating products (with [qrme](https://github.com/davidsbianchi1984/qrme)
> and [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version.
>
> ### What changed in the siblings
>
> - **QRME** — a profile front page (skills, experience, reviews, rating), a help
>   box on every screen that is structurally not a synthetic profile, and real
>   portraits on the screens that used to draw a generic orb.
> - **JIM-mini** — signal confidence for biometrics. `escalation.decide` always
>   took a `confidence` but only forecasts supplied one, so a measurement was a
>   fact by virtue of arriving; a reading the system does not trust now caps at
>   `check_in` instead of ringing an emergency contact.
>
> ### Verification
>
> 192 tests green — the same 192, passing the same way, which is rather the point
> of a release that claims no functional change here. 81 routes. Version strings
> moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency
> versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Release prep v0.2.1 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/71
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.2.0...app-v0.2.1

## app-v0.2.0 — app-v0.2.0

- Published: 2026-07-25
- Commit: `640b7781db6f9ecaf8beb23fc1996a7802792f5c`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.2.0>

> **PDI v0.2.0** — the release where who answers a facility's gate stops being a
> deployment-wide guess and becomes the tenant's own. One of three interoperating
> products (with [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version.
>
> ### Highlights
>
> - **`PDI_GATE_ONCALL` named one contact for the whole deployment.** In a
>   single-tenant install that is merely thin. In PDI it is wrong, because PDI is
>   multi-tenant: one vault, many customers, each with their own facility. A
>   courier at customer A's loading dock was handed off to a name belonging to
>   whoever set the environment variable — in a colocation facility, the operator
>   rather than the tenant. Everything else in this product is scoped to a tenant
>   and enforced by a token. The one name a stranger at a door got routed to was
>   global.
>
> - **The roster is per tenant, in the database**, written with the tenant's own
>   write token — the same authority as placing a beacon. `POST /gate/roster`,
>   `GET /gate/roster`, `DELETE /gate/roster/{id}`, `PUT /gate/timezone`. A
>   tenant with no roster still gets `PDI_GATE_ONCALL`, so nothing already
>   deployed changes.
>
> - **Validation happens on write**, which is the interesting difference from
>   JIM-mini's `jim/rota.py`. That module solves the same who-is-on-shift problem
>   but has to parse its rota out of an environment variable at the moment
>   somebody needs help — which is why it needs a never-raises read path and a
>   loud degradation story. PDI has an API, so a malformed shift is a **422 an
>   operator reads in daylight** and the bad rota never reaches the door. Same
>   property, bought with a gate instead of a guard.
>
> - **Three things it is careful about**, each a way of paging the wrong person:
>
>   - **Shifts cross midnight.** `18:00–06:00` is the shift a facility gate
>     exists for, and `start <= now <= end` is false for every minute of it. A
>     wrapping shift is two intervals and belongs to the day it *started*: at
>     02:00 on Saturday it is Friday's night porter on the desk, not the weekend
>     rota.
>   - **A facility is somewhere.** Each tenant sets its own IANA zone, and an
>     unknown one is **refused** rather than quietly read as UTC — the silent
>     version is wrong by the offset, and by a *different* offset in summer, so
>     it looks correct for half the year.
>   - **A rota has gaps.** The gate then tries everybody rather than nobody, and
>     reports `on_shift: false` on the page *and in the envelope*, so whoever it
>     wakes knows they were a guess.
>
> - **A failed page moves to the next name.** With one contact, a webhook that
>   rejected the page was the end of the line — trying the second is the entire
>   point of having a second. Every attempt is its own row, so the morning list
>   shows who was tried and in what order rather than one entry saying *failed*.
>
> - **Roster changes land on the audit chain** as `gate.roster`: who can be
>   summoned to a controlled facility is a governance fact, not a preference.
>
> ### Also
>
> Only one workflow writes the release body now. `desktop-release.yml` published
> `RELEASE_NOTES.md` verbatim — preamble and all — two to four minutes after
> `sync-release-notes.yml` had already published it correctly, so the build
> always won and every release needed re-syncing by hand.
>
> ### Verification
>
> 192 tests green (15 new this release). 81 routes. Tenant scoping is tested by
> trying to read and delete another tenant's roster, and by ringing two tenants'
> gates and asserting each reaches its own person — both fail if the scoping is
> removed. Version strings moved in exactly five places.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Only one workflow writes the release body now by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/69
> * A per-tenant on-call roster, and v0.2.0 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/70
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.9...app-v0.2.0

## app-v0.1.9 — app-v0.1.9

- Published: 2026-07-25
- Commit: `1062b91014e0955afffc4f3357c8579f3af832b5`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.9>

> **PDI v0.1.9** — the release where handing off at the gate stops meaning
> *writing a name down*. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
> together at this version.
>
> ### Highlights
>
> - **A hand-off reaches a person now.** The agent at the gate could always hand
>   off. What it could not do was *tell anybody*: `handed_to` recorded the on-call
>   contact, the ring went to `handed_off`, and somebody could stand at a door at
>   2am waiting for a person who did not know they were there. An escalation that
>   escalated to a database row.
>
> - **PDI ships no vendor.** It cannot know how a deployment reaches its people —
>   a manned NOC, one on-call phone, a pager system, a chat webhook — so it posts
>   a signed JSON envelope to `PDI_NOTIFY_URL` and stops. No SDK, no account, and
>   the same envelope shape JIM-mini uses, so an operator running both can point
>   them at one receiver.
>
> - **The sentence that made this worth building.** Every scripted hand-off says
>   some version of *I've passed this to the on-call contact* — which a person at
>   a door reads as **someone now knows I am here**. When the page does not go
>   out, that reading is false, and the cost of it is somebody waiting outside in
>   the dark. So the reply carries `reached_somebody: false` and an
>   `unreached_note`, and the scan page renders it as its own warning above the
>   *Passed to* row. Not as a clause at the end of a paragraph, and not by editing
>   words a model may have written.
>
> - **A page never fails a ring.** The caller gets their answer whether or not the
>   webhook answered; a dead webhook is recorded rather than raised. The envelope
>   inherits the beacon's blindness — kind, outcome, and where to read the rest
>   under the tenant's own token, with **not even the caller's own note**, which
>   is free text typed by a stranger and belongs in the sealed transcript rather
>   than in an outbound webhook that may be a third-party chat room. A test reads
>   the whole envelope as one string and looks for the filename, the counterparty,
>   the classification and the caller's words in it.
>
> - **Three audit actions rather than one** — `agent.page`, `agent.page_queued`,
>   `agent.page_failed` — because *a human was told* and *a human was not told*
>   are the two things an auditor is actually asking about, and one action would
>   have hidden the second inside the first. An expected delivery pages nobody at
>   all: waking the on-call for a parcel that was booked in is how a pager becomes
>   something people ignore.
>
> - **Unconfigured stays supported.** With no URL the page is `queued` — exactly
>   what the gate did before — except it is now a row
>   `GET /gate/pages?undelivered_only=true` can list rather than an absence nobody
>   could see. `GET /gate/channel` says whether a page can go out at all, without
>   revealing the URL, so it is checkable in the afternoon rather than at 3am.
>
> - **The tandem doc was describing a past release** — and missing this
>   repository's own arrow. `pdi/qrme_client.py`'s docstring cited *"every arrow
>   in docs/tandem.md points into PDI"* while being the thing that made it false.
>   [docs/tandem.md](docs/tandem.md) is now identical byte-for-byte in all three
>   repos, with a `pdi ✕ qrme` section, a beacon-family section, and
>   `docs/diagrams/tandem-flow.svg` generated rather than hand-drawn.
>
> ### Verification
>
> 177 tests green (11 new this release). 78 routes. Version strings moved in
> exactly five places: `pyproject.toml`, the FastAPI app, `app/package.json`, and
> the two root entries in its lockfile (dependency versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Custody beacons and the agent at the gate by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/62
> * sync-release-notes: read the tag's notes, and stop duplicating What's Changed by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/63
> * Generate the three README illustrations instead of hand-building them by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/64
> * A phone that scans a custody beacon gets a page, not JSON by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/65
> * A gate hand-off reaches a person, and v0.1.9 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/66
> * tandem.md: JIM's test count by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/67
> * Screen 38 stopped where the feature used to stop by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/68
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.8...app-v0.1.9

## app-v0.1.8 — app-v0.1.8

- Published: 2026-07-25
- Commit: `0fdc260c1a0986f4a90fc37a162eba6948a43e3c`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.8>

> **PDI v0.1.8** — cut alongside QRME and JIM-mini, as the three always
> are now. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three at this
> version.
>
> ### What changed in PDI
>
> **Nothing functional.** No API, no schema, no behaviour moved, and the vault seals and opens exactly what it did at 0.1.7.
>
> The only change here is a repair to the changelog itself: `[0.1.5]` and
> `[0.1.6]` linked to release tags that were never pushed, so both were 404s.
> They now point at their release-prep commits. Deliberately *not* fixed by
> backfilling those tags — pushing them now would fire the installer build and
> publish two superseded releases dated *after* v0.1.7, at the top of the page
> people download from. [docs/releasing.md](docs/releasing.md) records that
> reasoning, because an unexplained gap in a tag sequence is exactly what someone
> later "fixes" without knowing why it was left.
>
> **If you are already running 0.1.7, this upgrade is optional.** Take it to keep
> the three products reporting matching versions; skip it and you lose nothing.
>
> ### What is in the suite at 0.1.8
>
> The substance is QRME's: a live desk stops being only something you watch. You
> can ask to come up on the stream — which the host has to grant, and which needs
> a verified adult on a rated desk — and the room's comments, likes, shares and
> gifts render *on* the picture rather than beside it. See
> [QRME's notes](https://github.com/davidsbianchi1984/qrme/releases). Nothing in
> it asked PDI to change.
>
> ### Verification
>
> 134 tests green — the same 134, passing the same way, which is rather the
> point of a release that claims to change nothing functional. Version strings
> moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency
> versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * sync-release-notes: publish the release body from RELEASE_NOTES.md by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/50
> * Hosting posture: open admin fails closed off-machine, pairing knows its public URL by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/51
> * Key custody: a published deployment refuses an ephemeral key by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/52
> * Deployable as one container, and docs/hosting.md: who holds the key by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/53
> * BYOK: a tenant can hold a key the operator does not by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/54
> * Compile the native apps in CI, and fix the invalid iOS project spec by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/55
> * Release prep v0.1.5 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/56
> * Align the version with the suite: v0.1.6 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/57
> * Write down the release convention: the three cut together by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/58
> * Release prep v0.1.7: version bumps, changelog cut, release notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/59
> * Point the untagged versions at commits, not missing releases by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/60
> * Release prep v0.1.8: version bumps, changelog cut, release notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/61
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.4...app-v0.1.8

## app-v0.1.7 — app-v0.1.7

- Published: 2026-07-25
- Commit: `d74299757ce579673a4a3069ffff18d3d4742fe9`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.7>

> **PDI v0.1.7** — the first release cut under the new rule that the three
> products ship as one. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three at this
> version.
>
> ### What changed in PDI
>
> **Documentation only. No API, no schema, no behaviour change.**
>
> [docs/releasing.md](docs/releasing.md) now records how the three products are
> released, so the next round does not have to rediscover it:
>
> - **They are versioned as one release** — same number, same pass, even when a
>   repository has nothing of its own to ship that round.
> - **A repository with nothing to ship still cuts, and says so** in those words.
>   A note that inflates an empty round teaches people to skim the ones that are
>   not empty.
> - **Tag the release-prep commit, not the tip of `main`.** Work keeps landing
>   while a release is cut, and anything arriving after the changelog is
>   sectioned belongs under `[Unreleased]` rather than to the version being
>   tagged.
>
> That last rule is written down because it already nearly bit: QRME's v0.1.6 tag
> point sits behind its `main`, and tagging the tip would have published features
> under notes that do not mention them.
>
> Through v0.1.5 each repository cut whenever it happened to have work, so the
> numbers matched only by coincidence — which is how QRME reached 0.1.6 alone
> while this one sat at 0.1.5. v0.1.6 aligned them by hand; this is the first
> round where the alignment is the process rather than a correction.
>
> **If you are already running 0.1.6, this upgrade is optional.** Take it to keep
> the three products reporting matching versions; skip it and you lose nothing.
>
> ### What is in the suite at 0.1.7
>
> The substance this round is QRME's: live desks left behind as printed codes, a
> full audience layer (like, comment, share, subscribe), and a marketplace that
> can finally take payments. See
> [QRME's notes](https://github.com/davidsbianchi1984/qrme/releases). Nothing in
> it asked PDI to change.
>
> ### Verification
>
> 134 tests green — the same 134, passing the same way, which is rather the
> point of a release that claims to change nothing functional. Version strings
> moved in exactly five places: `pyproject.toml`, the FastAPI app,
> `app/package.json`, and the two root entries in its lockfile (dependency
> versions untouched).
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * sync-release-notes: publish the release body from RELEASE_NOTES.md by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/50
> * Hosting posture: open admin fails closed off-machine, pairing knows its public URL by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/51
> * Key custody: a published deployment refuses an ephemeral key by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/52
> * Deployable as one container, and docs/hosting.md: who holds the key by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/53
> * BYOK: a tenant can hold a key the operator does not by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/54
> * Compile the native apps in CI, and fix the invalid iOS project spec by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/55
> * Release prep v0.1.5 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/56
> * Align the version with the suite: v0.1.6 by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/57
> * Write down the release convention: the three cut together by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/58
> * Release prep v0.1.7: version bumps, changelog cut, release notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/59
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.4...app-v0.1.7

## app-v0.1.4 — PDI v0.1.4

- Published: 2026-07-24
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.4>

> **PDI v0.1.4** — run it your way: one command prints every way to run
> the vault console and you pick the device — your phone (scan a QR
> straight off the terminal), this PC, a packaged installer, or the
> headless API. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### Highlights
>
> - **`python -m pdi` — the launcher menu** — every way to run the vault
>   console, one command each, so you choose per device: `phone` (the QR
>   flow below), `desktop` (the Electron app on this PC), the packaged
>   installer (no toolchain needed), or `serve` (the headless API alone).
>   Same backend, same data, same token checks behind every door — admin
>   endpoints still require `PDI_ADMIN_TOKEN`.
> - **`python -m pdi phone` — the whole phone setup in one command** —
>   builds the console if it's missing (first-run `npm install` included),
>   prints the pairing URL **with a QR code drawn straight into the
>   terminal**, and serves on your local network. Scan, Add to Home
>   Screen, done.
> - **The console on your phone** — the API serves the built operator console at
>   `/app` (one origin for UI and API — nothing to configure on the phone);
>   `GET /pair` returns the URL on your local network with a scannable QR,
>   and the console installs to the home screen as a standalone app with a
>   thumb-reachable bottom tab bar. Local network only, by design; the
>   service worker never caches API traffic, so sealed records and audit
>   state are always live.
> - **Terms of Service** — docs/terms.md (v1.0): B2B service terms framing
>   PDI as encrypted data-custody infrastructure, not advice — the
>   Customer owns its data and answers for its lawfulness, consents,
>   tenant-token safekeeping, and connected systems; as-is warranty
>   disclaimer and liability cap. Served versioned at `GET /terms`;
>   provisioning a tenant records the version in force
>   (`terms_version`/`terms_accepted_at`) as the receipt.
> - **BAA, executed per customer and enforced in code** — the signable
>   template (docs/baa-template.md) carries the required § 164.504(e)
>   provisions plus an exhibit mapping each promise to the PDI control
>   that keeps it. The operator records each customer's executed BAA
>   (`POST /tenants/{id}/baa`); HIPAA-program transfers and intakes are
>   refused (403) for tenants without an active record; termination
>   re-imposes the block; executions land in the audit chain.
> - **Signed, notarized builds wired** — hardened runtime + entitlements +
>   notarization in the electron-builder config: adding the Apple/Windows
>   signing secrets produces Gatekeeper-clean, SmartScreen-friendly
>   installers. docs/releasing.md walks through obtaining the certificates.
>
> ### Verification
>
> 105 tests green; the desktop console builds clean; the cross-product
> suite smoke (run from qrme) passes end to end.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> `python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md

## app-v0.1.3 — PDI v0.1.3

- Published: 2026-07-24
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.3>

> **PDI v0.1.3** — the trust release: B2B service terms with a per-tenant
> receipt, and a Business Associate Agreement the vault enforces in code.
> One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### Highlights
>
> - **Run it on your phone** — the API serves the built operator console at
>   `/app` (one origin for UI and API — nothing to configure on the phone);
>   `GET /pair` returns the URL on your local network with a scannable QR,
>   and the console installs to the home screen as a standalone app with a
>   thumb-reachable bottom tab bar. Local network only, by design; the
>   service worker never caches API traffic, so sealed records and audit
>   state are always live.
> - **Terms of Service** — docs/terms.md (v1.0): B2B service terms framing
>   PDI as encrypted data-custody infrastructure, not advice — the
>   Customer owns its data and answers for its lawfulness, consents,
>   tenant-token safekeeping, and connected systems; as-is warranty
>   disclaimer and liability cap. Served versioned at `GET /terms`;
>   provisioning a tenant records the version in force
>   (`terms_version`/`terms_accepted_at`) as the receipt.
> - **BAA, executed per customer and enforced in code** — the signable
>   template (docs/baa-template.md) carries the required § 164.504(e)
>   provisions plus an exhibit mapping each promise to the PDI control
>   that keeps it. The operator records each customer's executed BAA
>   (`POST /tenants/{id}/baa`); HIPAA-program transfers and intakes are
>   refused (403) for tenants without an active record; termination
>   re-imposes the block; executions land in the audit chain.
> - **Signed, notarized builds wired** — hardened runtime + entitlements +
>   notarization in the electron-builder config: adding the Apple/Windows
>   signing secrets produces Gatekeeper-clean, SmartScreen-friendly
>   installers. docs/releasing.md walks through obtaining the certificates.
>
> ### Verification
>
> 101 tests green; the desktop console builds clean; the cross-product
> suite smoke (run from qrme) passes end to end.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> the backend from source — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * Run the PDI console from your phone: served console, pairing, installable PWA by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/46
> * Release prep v0.1.3: version bumps, changelog cut, release notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/47
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.2...app-v0.1.3

## app-v0.1.2 — PDI v0.1.2

- Published: 2026-07-24
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.2>

> **PDI v0.1.2** — the trust release: B2B service terms with a per-tenant
> receipt, and a Business Associate Agreement the vault enforces in code.
> One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### Highlights
>
> - **Terms of Service** — docs/terms.md (v1.0): B2B service terms framing
>   PDI as encrypted data-custody infrastructure, not advice — the
>   Customer owns its data and answers for its lawfulness, consents,
>   tenant-token safekeeping, and connected systems; as-is warranty
>   disclaimer and liability cap. Served versioned at `GET /terms`;
>   provisioning a tenant records the version in force
>   (`terms_version`/`terms_accepted_at`) as the receipt.
> - **BAA, executed per customer and enforced in code** — the signable
>   template (docs/baa-template.md) carries the required § 164.504(e)
>   provisions plus an exhibit mapping each promise to the PDI control
>   that keeps it. The operator records each customer's executed BAA
>   (`POST /tenants/{id}/baa`); HIPAA-program transfers and intakes are
>   refused (403) for tenants without an active record; termination
>   re-imposes the block; executions land in the audit chain.
> - **Signed, notarized builds wired** — hardened runtime + entitlements +
>   notarization in the electron-builder config: adding the Apple/Windows
>   signing secrets produces Gatekeeper-clean, SmartScreen-friendly
>   installers. docs/releasing.md walks through obtaining the certificates.
>
> ### Verification
>
> 94 tests green; the desktop console builds clean; the cross-product
> suite smoke (run from qrme) passes end to end.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> the backend from source — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * BAA template + macOS notarization wiring by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/42
> * BAA enforcement: executed per customer before production PHI, in code by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/43
> * Terms of Service: B2B service terms, served versioned, receipted per tenant by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/44
> * Release prep v0.1.2: version bumps, changelog cut, release notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/45
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.1...app-v0.1.2

## app-v0.1.1 — app-v0.1.1

- Published: 2026-07-24
- Commit: `main`
- Assets: 5
- Page: <https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.1>

> **PDI (Private Data Infrastructure) v0.1.1** — the vault goes enterprise and
> gets native apps everywhere. One of three interoperating products (with
> [qrme](https://github.com/davidsbianchi1984/qrme) and
> [jim-mini](https://github.com/davidsbianchi1984/jim-mini)).
>
> ### Highlights
>
> - **Native apps at parity** — iOS, Android, and Windows carry the whole
>   operator console: Overview (language, feedback, and **in-app admin key
>   management** — load / rotate / retire key versions with the deployment's
>   admin token, kept in memory only), Vault, Audit, Robots, Connectors,
>   Transfers, and Secure Intake.
> - **Enterprise compliance transfer** — HIPAA / OSHA / CPNI-grade secure file
>   transfer for corporations, plus **secure intake** so subscribers and
>   partner companies can send files *in* — sealed and audit-chained end to
>   end, receipts included.
> - **Robots as vault-backed data sources** — bind catalog robots, seal their
>   maps / snapshots / sensor logs on ingest, and keep tenant-owned custody
>   even after unbinding.
> - **Connected platforms** — all 16 suite connection platforms, the
>   Apple / Google / Microsoft / Canva connected-apps catalog, and
>   per-assistant screens for Apple Intelligence, Gemini, and Copilot.
> - **Language & provenance** — per-tenant language with hand-translated vault
>   notes in all supported languages, sign-in gateway choice, dictionary
>   translate, and sealed-record provenance (origin, seal details, audit
>   trail).
> - **Positions / assistant builder** — the AI-integration & role-mapping
>   questionnaire that blueprints an assistant for any industry role.
> - **Starter vault** — a seeded demo tenant with sealed records covering every
>   provenance origin and a full custody cycle to explore.
> - **Two form factors documented** — every capability screen now renders in
>   both the phone frame and a wide desktop operator-console frame.
> - **First-run onboarding** — welcome → provider login → key setup → token
>   grant → connected systems → all set.
>
> ### Verification
>
> 88 tests green; live-server smoke flows pass (seal / read / audit-verify);
> the desktop app builds clean; the cross-product suite smoke (run from qrme)
> passes end to end.
>
> ### Install
>
> Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
> the backend from source — see the [README](README.md). Installers are signed
> only if signing secrets are configured; otherwise they are unsigned (see
> [docs/releasing.md](docs/releasing.md)).
>
> **Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
>
>
> ## What's Changed
> * README: fix two paste artifacts (Infrastructure" enabling; Tasks) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/16
> * Add Apple/Google/email Log In screen by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/17
> * Add first-run onboarding flow (Welcome → Key Setup → Grant → Connect → All Set) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/18
> * Record post-0.1.0 onboarding screens in the changelog by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/19
> * Social connectors: collect into the vault, publish/run via QR beacons by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/20
> * Support all 16 connection platforms from the suite set by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/21
> * Connected-apps catalog: Apple, Google, Microsoft & Canva connectors by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/22
> * App connectors: connect a catalog app and use it (collect · act · produce) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/23
> * Enterprise compliance-grade secure file transfer (HIPAA, OSHA, CPNI, …) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/24
> * Inbound compliant intake: subscribers & partner companies send files IN by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/25
> * Add Secure Intake screen (31) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/26
> * Add simple Files & Photos device-connector screen (32) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/27
> * Add per-assistant screens: Apple Intelligence, Google Gemini, Microsoft Copilot by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/28
> * Add native iOS/Android/Windows apps for PDI Vault by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/29
> * Robots as vault-backed data sources (catalog, sealed ingest, custody) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/30
> * Native apps: add the Robots screen (vault-backed data sources) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/31
> * Native apps: add the Transfers screen (compliance-grade secure transfer) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/32
> * Native apps: add Secure Intake (the inbound half of compliance transfer) by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/33
> * Native apps: add platform Connectors, grouped with Robots under Sources by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/34
> * Per-tenant language + sealed-record provenance by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/35
> * Hand-translate vault notes into all supported languages by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/36
> * Language at the sign-in gateway, delivery modes, and dictionary translate by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/37
> * Seed the starter vault: a demo tenant with sealed records to explore by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/38
> * Help us improve: in-app product feedback anyone can send by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/39
> * Desktop-frame gallery, in-app admin key rotation, chrome l10n + polish by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/40
> * Release prep v0.1.1: version bumps, changelog & notes by @davidsbianchi1984 in https://github.com/davidsbianchi1984/pdi/pull/41
>
>
> **Full Changelog**: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.0...app-v0.1.1

