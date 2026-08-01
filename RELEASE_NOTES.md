# PDI v0.23.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.23.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.23.0 — the recipient had nowhere to put their token.**

`receive_transfer` names its caller: *"The recipient retrieves the file with
their receive token — no tenant credential; the token itself is the (auditable)
authorization."* They were sent a file under HIPAA or OSHA or CPNI. They hold a
one-shot token in an email. They are not a tenant and never will be.

The only thing calling that route was the console's **"Receive it as the
recipient"** button — the *sender* rehearsing, disabled unless their own
session still held the receipt.

**There is now a page at `/r/{id}`.** The token rides in the URL fragment,
which browsers never send to a server, so the link survives mail and proxies
without leaving a one-shot authorization for compliance-grade material in
anybody's access log. It is cleared from the address bar once read. The page
renders for any id, because a 404 would turn the route into a way of asking
which transfer ids are real.

Then the door guards caught the thing that mattered most: the page could not be
linked to. The sender had no way to produce the URL at all — the same defect
one step earlier in the same flow. **Copy the recipient's link** resolves the
page before handing it over, because a misconfigured public base would
otherwise be discovered by the recipient, who has nobody to ask.

Android and Windows can also read back the vault keys a bound robot has sealed.
Sealing hands one key back, once; close the app and the server was the only
thing that still knew it.

This release also corrects one of this repository's own guards, which had
asserted that the console reaches the receive route and concluded PDI had got
it right. Both facts were true and the conclusion was wrong: the absence of a
sign-in gate was never the recipient having access, it was the recipient having
nothing to be gated out of.

**Suite: 372 passing.**
