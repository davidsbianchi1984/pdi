"""The page somebody lands on after scanning a custody beacon.

`GET /s/{id}` answered JSON, which meant a phone's camera app opened it and
showed a courier a wall of braces. This is the page that should have been
there.

The constraints are why this is hand-written HTML rather than a route into the
console:

* **It opens inside a camera app's in-app browser**, on cellular, from a cold
  start, possibly in a loading bay with one bar. So it is one self-contained
  document — inline CSS, inline script, no font, image or stylesheet fetches.
  Nothing about it needs a second request to be legible.
* **The reader is a stranger**: a courier, a warehouse clerk, somebody who
  found a drive on a train. No token, no session, no idea what PDI is. The
  page has about a second to say what the thing in their hands is and what to
  do with it.
* **And a stranger in their own language.** Every other localization path in
  this vault takes a ``tenant_id`` — right for the API, whose callers are all
  tenants, and useless here, where nobody has one. These four pages therefore
  key on the reader's ``Accept-Language`` header, which their browser has been
  sending all along. Text is looked up through :func:`pdi.i18n.tr_page` at the
  point it is written, so the English stays legible in the source.
* **It must not become a disclosure.** Everything :mod:`pdi.beacons` withholds,
  this withholds — the card renders what `seal_card` returns and nothing more,
  so there is no second place for the contents to leak from.

The form posts to a **relative** URL. An absolute one baked from
``PDI_PUBLIC_URL`` breaks every scan on a LAN deployment, which is most of them
while anybody is testing.
"""

from __future__ import annotations

from . import pagehead

import html
import json

from . import i18n

# Night indigo and vault cyan — the console's palette, and the dark ink the
# printed QR is rendered in.
_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0c0920;color:#f2effc;min-height:100dvh;display:flex;
 align-items:center;justify-content:center;padding:20px;
 font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 -webkit-font-smoothing:antialiased}
.card{width:100%;max-width:440px}
.seal{background:#181240;border:1px solid #302a60;border-radius:20px;
 padding:22px;box-shadow:0 20px 50px rgba(0,0,0,.5);
 animation:rise .5s cubic-bezier(.2,.8,.2,1) both}
/* Transform only — never opacity. If the animation does not run at all (an
   in-app browser that drops it, reduced motion, a print view), the card must
   still be on screen. A page whose job is to be legible in one second cannot
   have its visibility depend on an effect. */
@keyframes rise{from{transform:translateY(10px)}to{transform:none}}
@media (prefers-reduced-motion:reduce){.seal{animation:none}}
/* A full sentence, so a banner rather than a pill: a rounded capsule with two
   wrapped lines in it reads as a mistake. */
.badge{display:block;font-size:12.5px;font-weight:700;letter-spacing:.2px;
 line-height:1.45;color:#7dd3fc;border:1px solid rgba(56,189,248,.55);
 border-radius:12px;padding:9px 12px;margin-bottom:16px}
h1{font-size:21px;line-height:1.25;margin-bottom:4px}
.ref{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;
 color:#9a93c6;word-break:break-all;margin-bottom:16px}
.row{display:flex;justify-content:space-between;gap:12px;padding:10px 0;
 border-top:1px solid #262046;font-size:14px}
.row span:first-child{color:#9a93c6}
.row span:last-child{text-align:right;font-weight:600}
.progs{display:flex;flex-wrap:wrap;gap:6px;justify-content:flex-end}
.prog{font-size:11px;font-weight:700;letter-spacing:.4px;color:#ffb84d;
 border:1px solid rgba(255,184,77,.5);border-radius:999px;padding:3px 8px}
.note{color:#9a93c6;font-size:13.5px;margin-top:16px}
.never{margin-top:14px;padding:12px 14px;border-radius:12px;
 background:rgba(224,104,122,.08);border:1px solid rgba(224,104,122,.35);
 color:#f0b8c1;font-size:13.5px}
label{display:block;font-size:13px;color:#9a93c6;margin:14px 0 6px}
input,select,textarea{width:100%;font:inherit;font-size:16px;color:#f2effc;
 background:#0f0b28;border:1px solid #302a60;border-radius:12px;
 padding:12px 14px;-webkit-appearance:none}
input:focus,select:focus,textarea:focus{outline:2px solid #38bdf8;
 outline-offset:-1px}
button{width:100%;margin-top:18px;font:inherit;font-size:16px;font-weight:700;
 color:#04121c;background:linear-gradient(90deg,#38bdf8,#7dd3fc);border:0;
 border-radius:14px;padding:15px;cursor:pointer}
button:disabled{opacity:.55;cursor:default}
input[type=text]{width:100%;font:inherit;font-size:16px;color:#f2effc;
 background:#120e2c;border:1px solid #302a60;border-radius:12px;
 padding:12px 14px;-webkit-appearance:none;box-sizing:border-box}
input[type=text]:focus{outline:2px solid #7b5cff;outline-offset:-1px}
input[type=text]:disabled{opacity:.6}
a.dl{display:block;margin-top:14px;text-align:center;font-weight:700;
 color:#fff;background:linear-gradient(90deg,#5b3ce0,#7b5cff);
 border-radius:13px;padding:15px;text-decoration:none}
#file h2{font-size:16px;margin:16px 0 4px;color:#f2effc;word-break:break-all}
.status{min-height:20px;margin-top:12px;font-size:13.5px;color:#7dd3fc;
 text-align:center}
.foot{color:#6a6399;font-size:12px;text-align:center;margin-top:18px}
"""


def _page(title: str, body: str, language: str = "en") -> str:
    # `lang` is not decoration: a screen reader picks its voice from it, and
    # some of these pages are read by somebody with a parcel in both hands.
    # `dir` because Arabic is one of the ten languages this vault supports and
    # a right-to-left page laid out left-to-right is unreadable, not merely
    # untranslated.
    direction = "rtl" if language == "ar" else "ltr"
    return (
        f'<!doctype html><html lang="{html.escape(language)}" '
        f'dir="{direction}">'
        '<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,'
        'viewport-fit=cover"><meta name="theme-color" content="#0c0920">'
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
        f'<body><main class="card">{body}</main></body></html>')


# The characters that can end a `<script>` element early, or end a JavaScript
# string literal, written as the \uXXXX escapes JavaScript reads back as the
# original character — so the value survives intact and an HTML parser cannot
# mistake any of it for markup. In JSON these four appear only inside string
# values, never in the structure, so rewriting them in the serialised text is
# safe for any shape. U+2028 and U+2029 are JavaScript line terminators and
# end a string literal where `ensure_ascii=False` leaves them raw.
_JS_HAZARDS = {
    "<": "\\u003c", ">": "\\u003e", "&": "\\u0026",
    "\u2028": "\\u2028", "\u2029": "\\u2029",
}


def _js_literal(obj) -> str:
    """Any JSON value, safe to drop **inside a `<script>` element**.

    The one primitive both `_js` and `_strings` are built on, because they had
    drifted apart: one escaped for the element and the other did not, and the
    difference was invisible at every call site.

    `json.dumps` escapes what would end a JavaScript *string*. It has nothing
    to say about `</script`, which ends the *element* whatever the JavaScript
    quoting says — so the value closes the page's own nonced script and
    everything after it is parsed as markup.

    Deliberately **not** `html.escape`. A browser does not decode HTML
    entities inside a script element, so escaping there protects nothing and
    corrupts the value: `Terms & Conditions` reached the reader as
    `Terms &amp; Conditions`, and this is what the translated string table is
    built on.

        asked     is the value escaped
        mattered  is it escaped for the place it lands

    The page was safe by accident rather than by the mechanism written for
    it. The `.replace("</", "<\\/")` above — the guard against a literal
    `</script` ending the element, which is the hazard this docstring names —
    sat *after* an `html.escape` that had already turned `<` into `&lt;`. It
    never matched anything and never could.
    """
    text = json.dumps(obj, ensure_ascii=False)
    for char, escape in _JS_HAZARDS.items():
        text = text.replace(char, escape)
    return text


def _js(value: str) -> str:
    """A JS string literal safe to drop into an inline script.

    `json.dumps` alone is not enough, and the difference is the whole reason
    this function exists. Inside a `<script>` element the HTML parser ends the
    element at the first `</script`, **whatever the JavaScript quoting says**
    — so a value containing `</script>` closes the script early and everything
    after it is parsed as markup. `json.dumps` escapes what would end a *JS
    string*; it has nothing to say about what ends an *HTML element*.

    QRME had this right and this product did not, for the reason 0.59.1 named
    about a floor and 0.59.0 about a literal: a helper written once and copied
    into three repositories drifts, and the copy that drifted was the one
    whose entire job is to be safe. No route here currently passes a
    caller-supplied string through it — the values are database identifiers
    and translated constants, and a path segment cannot carry `</script>`
    because the slash breaks routing — so this is a latent hole rather than a
    live one. It is fixed anyway: the next value somebody escapes with this is
    exactly the one it was written for.
    """
    return _js_literal(value)


def _strings(language: str, **english: str) -> str:
    """The script's own words, translated, as a JSON object literal.

    `ensure_ascii=False` because the page already declares UTF-8 and the
    escaped form triples the size of every non-Latin blob — on a page whose
    whole premise is one cold request in a loading bay with one bar.
    """
    return _js_literal({name: i18n.tr_page(text, language)
                        for name, text in english.items()})

def _t(language: str):
    """A lookup bound to one reader's language.

    The English literal stays at the call site rather than moving to a table
    of keys, so this file still reads as the page it renders. `tr_page` falls
    back to English for anything it does not have, and the test beside it is
    what notices a sentence that arrived without translations.
    """
    return lambda text: i18n.tr_page(text, language)


# The long sentences, named where a call site would otherwise wrap four times.
GONE_NOTE = ("It may have been retired, or it may never have been one of "
             "ours. Either way there is nothing here to see, and nothing you "
             "need to do.")
NO_HOLDER = ("Report it here and the holder will be told \u2014 you won't "
             "learn whose it is, and you don't need to.")
CANNOT_OPEN = ("This code cannot open it, and neither can whoever is holding "
               "it. It says the thing is sealed \u2014 never what is inside.")
FOUND_FOOT = ("Your report is timestamped and hash-chained into this "
              "carrier's chain of custody. It cannot be altered afterwards "
              "\u2014 including by us.")
GATE_FOOT = ("Whoever answers cannot let anyone in \u2014 that decision "
             "always belongs to a person. This exchange is recorded in the "
             "facility's audit chain.")
RECEIVE_NOTE = ("It was sent through PDI under a compliance program. "
                "Collecting it is recorded in the sender's chain of custody "
                "\u2014 that record is the point of sending it this way, and "
                "it names the collection, not you.")
RECEIVE_AGAIN = ("Keep the link if you need it again \u2014 the token stays "
                 "good, and every collection is written into the sender's "
                 "chain of custody, so a second one is visible rather than "
                 "silent.")

def gone(language: str = "en") -> str:
    """A code that never existed, or has been retired.

    One page for both, deliberately: somebody holding a phone at a dead
    sticker should not be able to tell which, or a retired code becomes a way
    of confirming that a particular reference once existed.
    """
    t = _t(language)
    headline = t("This code doesn't resolve to anything")
    return _page(t("Nothing here"), (
        '<div class="seal">'
        f"<h1>{html.escape(headline)}</h1>"
        f'<p class="note">{html.escape(t(GONE_NOTE))}</p></div>'), language)


def _rows(card: dict, language: str = "en") -> str:
    # The labels translate; the values do not. `state`, the program names and
    # the holder are the card's own data — translating a tenant's holder name
    # or a statute's short name would be inventing, not localizing.
    t = _t(language)
    progs = card.get("programs") or []
    out = [
        f'<div class="row"><span>{html.escape(t("State"))}</span>'
        f'<span>{html.escape(card.get("state") or "—")}</span></div>',
    ]
    if progs:
        chips = "".join(f'<span class="prog">{html.escape(p.upper())}</span>'
                        for p in progs)
        out.append(f'<div class="row"><span>{html.escape(t("Governed by"))}'
                   f'</span><span class="progs">{chips}</span></div>')
    if card.get("held_by"):
        out.append(f'<div class="row"><span>{html.escape(t("Held by"))}</span>'
                   f'<span>{html.escape(card["held_by"])}</span></div>')
    return "".join(out)


# `o.j.note` and `o.j.detail` win over the local strings when the server sends
# them, and now that is safe. The earlier note here said they arrive "through
# the response middleware, which is the tenant's language rather than the
# reader's", and treated that as a considered trade-off. It was not one: the
# middleware keys on the *calling* tenant and these calls have none, so the
# server's sentences were never localized into anything at all. They are now
# translated from the reader's own header, so preferring them costs nothing.
_FOUND_JS = """
(function(){
 var S=%(strings)s,
     f=document.getElementById('f'),b=document.getElementById('go'),
     s=document.getElementById('st');
 if(!f)return;
 f.addEventListener('submit',function(e){
  e.preventDefault();b.disabled=true;s.textContent=S.working;
  fetch(%(endpoint)s,{method:'POST',
   headers:{'content-type':'application/json'},
   body:JSON.stringify({where:document.getElementById('w').value||null,
                        contact:document.getElementById('c').value||null})})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
  .then(function(o){
   if(o.ok){b.remove();s.textContent=o.j.note||S.done;}
   else{b.disabled=false;s.textContent=(o.j&&o.j.detail)||S.failed;}
  }).catch(function(){b.disabled=false;s.textContent=S.offline;});
 });
})();
"""

_RING_JS = """
(function(){
 var S=%(strings)s,
     f=document.getElementById('f'),b=document.getElementById('go'),
     s=document.getElementById('st');
 if(!f)return;
 f.addEventListener('submit',function(e){
  e.preventDefault();b.disabled=true;s.textContent=S.working;
  fetch(%(endpoint)s,{method:'POST',
   headers:{'content-type':'application/json'},
   body:JSON.stringify({kind:document.getElementById('k').value,
                        note:document.getElementById('n').value||null})})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
  .then(function(o){
   if(o.ok){f.innerHTML='';
    var w=document.createElement('div');w.className='seal';
    w.innerHTML='<div class="badge">'+(o.j.ai_generated?S.ai:S.automated)
     +'</div><h1>'+esc(o.j.words||'')+'</h1>'
     +'<p class="note">'+esc(o.j.disclosure||'')+'</p>'
     /* Loud, and above the "Passed to" row rather than below it: the reply
        says somebody was told, and if nobody was, that is the sentence the
        person outside most needs and the one they are least likely to hunt
        for. */
     +(o.j.unreached_note?'<div class="never">'+esc(o.j.unreached_note)
       +'</div>':'')
     +(o.j.handed_to?'<div class="row"><span>'+S.passedto+'</span><span>'
       +esc(o.j.handed_to)+'</span></div>':'');
    f.parentNode.appendChild(w);s.textContent='';}
   else{b.disabled=false;s.textContent=(o.j&&o.j.detail)||S.failed;}
  }).catch(function(){b.disabled=false;s.textContent=S.offline;});
 });
 function esc(t){var d=document.createElement('div');d.textContent=t;
  return d.innerHTML;}
})();
"""


def seal_card_page(card: dict, language: str = "en") -> str:
    """A carrier: what it is, what governs it, and how to hand it in.

    Renders only what ``beacons.seal_card`` returned. There is no second
    lookup here and nothing is fetched to decorate it, so this page cannot
    disclose something the card itself withheld.
    """
    t = _t(language)
    ref = html.escape(card["reference"])
    held = card.get("held_by")
    # Translated whole and then filled, never a translated half joined to a
    # name: word order around a possessive differs across these ten
    # languages, and a sentence stitched from fragments reads as broken in
    # most of them. The same lesson the console learned when half its
    # untranslated backlog turned out to be sentence fragments.
    who = (t("This belongs to {holder}.").format(holder=html.escape(held))
           if held else html.escape(t(NO_HOLDER)))
    body = (
        '<div class="seal">'
        f'<div class="badge">{html.escape(card["badge"])}</div>'
        f"<h1>{html.escape(t('This is under custody'))}</h1>"
        f'<p class="ref">{ref}</p>'
        f"{_rows(card, language)}"
        f'<p class="note">{who}</p>'
        f'<div class="never">{html.escape(t(CANNOT_OPEN))}</div>'
        '<form id="f">'
        f'<label for="w">{html.escape(t("Where is it?"))}</label>'
        '<input id="w" name="w" autocomplete="off" '
        f'placeholder="{html.escape(t("depot 3, Oakland"), quote=True)}">'
        '<label for="c">'
        f'{html.escape(t("How can you be reached? (optional)"))}</label>'
        '<input id="c" name="c" autocomplete="off" '
        f'placeholder="{html.escape(t("name, phone"), quote=True)}">'
        '<button id="go" type="submit">'
        f'{html.escape(t("I found this"))}</button>'
        "</form>"
        '<div class="status" id="st"></div>'
        "</div>"
        f'<p class="foot">{html.escape(t(FOUND_FOOT))}</p>'
        + pagehead.script_open()
        + _FOUND_JS % {"endpoint": _js(f"/s/{card['reference']}/found"),
                       "strings": _strings(language, working="Recording…",
                                           done="Recorded. Thank you.",
                                           failed="That did not go through.",
                                           offline="No connection — try "
                                                   "again in a moment.")}
        + "</script>")
    return _page(t("Sealed carrier"), body, language)


def gate_page(card: dict, language: str = "en") -> str:
    """A facility gate: ring it, and see what answers.

    The reply renders in place rather than as a new page, because somebody
    standing at a door in the rain should not have to watch a navigation.
    """
    t = _t(language)
    ref = html.escape(card["reference"])
    # The option *values* stay English: they are the API's vocabulary and
    # `ring` matches on them. Only what a person reads is translated.
    kinds = (("delivery", "A delivery"), ("collection", "A collection"),
             ("access", "Access to the site"), ("other", "Something else"))
    options = "".join(
        f'<option value="{html.escape(value)}">{html.escape(t(label))}</option>'
        for value, label in kinds)
    body = (
        '<div class="seal">'
        f'<div class="badge">{html.escape(card["badge"])}</div>'
        f"<h1>{html.escape(t('Controlled facility'))}</h1>"
        f'<p class="ref">{ref}</p>'
        f"{_rows(card, language)}"
        f'<p class="note">{html.escape(card.get("note") or "")}</p>'
        '<form id="f">'
        f'<label for="k">{html.escape(t("What are you here for?"))}</label>'
        '<select id="k" name="k">'
        f"{options}"
        "</select>"
        '<label for="n">'
        f'{html.escape(t("Anything else we should know?"))}</label>'
        '<textarea id="n" name="n" rows="3" placeholder="'
        f'{html.escape(t("who you are, who you were expecting to meet"), quote=True)}'
        '"></textarea>'
        f'<button id="go" type="submit">{html.escape(t("Ring"))}</button>'
        "</form>"
        '<div class="status" id="st"></div>'
        "</div>"
        f'<p class="foot">{html.escape(t(GATE_FOOT))}</p>'
        + pagehead.script_open()
        + _RING_JS % {"endpoint": _js(f"/s/{card['reference']}/ring"),
                      "strings": _strings(language, working="Ringing…",
                                          ai="AI REPLY",
                                          automated="AUTOMATED",
                                          passedto="Passed to",
                                          failed="That did not go through.",
                                          offline="No connection — try again "
                                                  "in a moment.")}
        + "</script>")
    return _page(t("Controlled facility"), body, language)


def page_for(card: dict, language: str = "en") -> str:
    """The right page for whatever the code was placed on."""
    return (gate_page(card, language) if card.get("gate")
            else seal_card_page(card, language))


# --------------------------------------------------------------------------- #
# The recipient's page
# --------------------------------------------------------------------------- #
#
# `receive_transfer` says who its caller is: "The recipient retrieves the file
# with their receive token — no tenant credential; the token itself is the
# (auditable) authorization." That person is not a tenant. They were sent a
# file under HIPAA or OSHA or CPNI, they have a one-shot token in an email,
# and until this page existed they had nowhere to use it: the only caller of
# the route in the whole product was Exchange.tsx's "Receive it as the
# recipient" button, which is the *sender* rehearsing, disabled unless their
# own session still holds the receipt.
#
# **The token rides in the URL fragment.** `/r/{tid}#<token>` — browsers never
# send a fragment to a server, so a link that reaches an access log, a proxy,
# or a Referer header leaves the credential behind. A query string would put a
# one-shot authorization for a compliance-grade file into every log between
# here and the recipient. The field below is the fallback for somebody who has
# the token but not the link.

_RECEIVE_JS = """
(function(){
 var S=%(strings)s, tid=%(tid)s, box=document.getElementById('t'),
     b=document.getElementById('go'), out=document.getElementById('out'),
     st=document.getElementById('st');
 // Fragment first, and cleared from the address bar immediately. Not because
 // the token is one-shot — it is not, and the copy below was corrected once
 // already for saying so — but because a link that stays in the address bar
 // is a link over a shoulder, in a screenshot, and in the next person's
 // browser history.
 var frag=(location.hash||'').replace(/^#/,'');
 if(frag){box.value=decodeURIComponent(frag);
  history.replaceState(null,'',location.pathname);}
 b.addEventListener('click',function(){
  var tok=box.value.trim(); if(!tok)return;
  b.disabled=true;st.textContent=S.fetching;
  fetch('/transfers/'+encodeURIComponent(tid)+'/receive',
   {method:'POST',headers:{'x-receive-token':tok}})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
  .then(function(o){
   b.disabled=false;
   if(!o.ok){st.textContent=(o.j&&o.j.detail)||S.failed;return;}
   st.textContent='';
   var j=o.j, wrap=document.getElementById('file');
   document.getElementById('fn').textContent=j.filename||'file';
   if(j.programs&&j.programs.length){
    document.getElementById('pg').textContent=j.programs.join(' \\u00b7 ');}
   if(j.custody){document.getElementById('cu').textContent=j.custody;}
   // A download rather than a render: this is somebody else's compliance
   // material and the browser is not the right place to display it.
   //
   // `content` is whatever the sender sealed. The console base64s on the way
   // in and atob()s on the way out, but that is a console convention, not an
   // API contract — `POST /transfers` stores the string it is given. So this
   // decodes only when the candidate round-trips exactly, and hands over the
   // raw bytes otherwise. A file whose plaintext is itself valid base64 would
   // be decoded wrongly; that ambiguity is in the API, not here, and guessing
   // quietly is how a compliance file arrives corrupted.
   var raw=j.content||'', bytes=null;
   try{var dec=atob(raw); if(btoa(dec)===raw){
    bytes=Uint8Array.from(dec,function(c){return c.charCodeAt(0);});}}
   catch(e){/* not base64 — deliver it as sent */}
   var blob=new Blob([bytes||raw]);
   var a=document.getElementById('dl');
   a.href=URL.createObjectURL(blob);a.download=j.filename||'file';
   wrap.style.display='block';box.disabled=true;b.style.display='none';})
  .catch(function(){b.disabled=false;
   st.textContent=S.offline;});
 });
})();
"""


def receive_page(tid: str, language: str = "en") -> str:
    """Where somebody collects a file that was sealed for them.

    They are not a tenant and never will be. Everything here works with the
    receive token alone, which is what the route was built to accept — and,
    because there is no tenant, the language comes from the reader's browser
    rather than from a stored preference nobody here has ever set.
    """
    t = _t(language)
    body = (
        '<div class="seal">'
        f"<h1>{html.escape(t('A file was sealed for you'))}</h1>"
        f'<p class="note">{html.escape(t(RECEIVE_NOTE))}</p>'
        f'<label for="t">{html.escape(t("Your receive token"))}</label>'
        '<input id="t" type="text" autocomplete="off" spellcheck="false" '
        'placeholder="'
        f'{html.escape(t("from the message that sent you here"), quote=True)}">'
        f'<button id="go" type="button">{html.escape(t("Collect it"))}</button>'
        '<div class="status" id="st"></div>'
        '<div id="file" style="display:none">'
        '<h2 id="fn"></h2>'
        '<p class="note" id="pg"></p>'
        '<p class="note" id="cu"></p>'
        f'<a id="dl" class="dl">{html.escape(t("Download"))}</a>'
        # Written after driving it rather than before. The first draft said
        # "the token was one-shot; this link will not fetch it again". A
        # second POST returns 200. The route's own docstring calls the token
        # "the (auditable) authorization" — auditable, not single-use — and
        # every retrieval lands in the custody chain, which is the property
        # that actually holds. Shipping the first version would have been this
        # page repeating the exact mistake the audit that produced it keeps
        # finding: copy asserting something the system does not do.
        f'<p class="note">{html.escape(t(RECEIVE_AGAIN))}</p>'
        "</div>"
        "</div>"
        + pagehead.script_open()
        + _RECEIVE_JS % {
            "tid": _js(tid),
            "strings": _strings(language, fetching="Fetching…",
                                failed="That did not work.",
                                offline="No connection — the link is "
                                        "still good, try again.")}
        + "</script>")
    return _page(t("A file was sealed for you"), body, language)
