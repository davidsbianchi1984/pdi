# PDI v0.3.3 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.3.3` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.3.3** — **no functional change to the vault in this release**: no new
routes, no schema, no behaviour. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

The round belongs to the console.

### The agent status light, where amber means someone is at a door

Green *working*, amber *needs you*, red *stopped*. On most surfaces amber is an
abstraction; here it is a person standing outside, waiting to be let in.

Screen 38 showed one gate agent, and nothing showed all of them — which on a
site with a dozen entrances is the wrong shape. **Screen 39** groups them by
light, so the amber group is the row a thumb lands on without aiming.

**The overlay** rides over an ordinary view and over **every** desktop view. A
console is watched from, not visited, and leaving an amber gate agent sitting
on a screen nobody is looking at is the worst version of the problem this
exists to solve. It is shaped like the watch face rather than as a bar across
the screen: a small translucent box in the corner, three stacked rows, each its
own tap target.

The mapping lives once, in QRME's `agentlight.py`, for all three products.

### The README leads with the console screens now

Everything you can look at is above everything you have to read, and the
run / config / API material is gathered under one **Reference** heading at the
bottom — so a command spotted in a screenshot has one place to go and look it
up. Those tables are set smaller, because they are for looking things up in
rather than reading through.

### Also fixed

- Screen 38 said "loading dock facility beacon", which said nothing. The rows
  now describe what is actually happening: someone at the door, a delivery
  directed round to goods-in, somebody who wants to be let in.
- The README claimed 38 desktop-frame counterparts. There are 40.

### Verification

192 tests green. Console screens regenerated across all three mobile platforms
and the desktop console for macOS and Windows.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.3.3` tag), or run `python -m pdi`.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
