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
* **It must not become a disclosure.** Everything :mod:`pdi.beacons` withholds,
  this withholds — the card renders what `seal_card` returns and nothing more,
  so there is no second place for the contents to leak from.

The form posts to a **relative** URL. An absolute one baked from
``PDI_PUBLIC_URL`` breaks every scan on a LAN deployment, which is most of them
while anybody is testing.
"""

from __future__ import annotations

import html
import json

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
.status{min-height:20px;margin-top:12px;font-size:13.5px;color:#7dd3fc;
 text-align:center}
.foot{color:#6a6399;font-size:12px;text-align:center;margin-top:18px}
"""


def _page(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,'
        'viewport-fit=cover"><meta name="theme-color" content="#0c0920">'
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
        f'<body><main class="card">{body}</main></body></html>')


def _js(value: str) -> str:
    """A string safe to drop into inline script — json.dumps escapes the
    quotes and anything else that would end the literal early."""
    return json.dumps(value)


def gone() -> str:
    """A code that never existed, or has been retired.

    One page for both, deliberately: somebody holding a phone at a dead
    sticker should not be able to tell which, or a retired code becomes a way
    of confirming that a particular reference once existed.
    """
    return _page("Nothing here", (
        '<div class="seal">'
        "<h1>This code doesn't resolve to anything</h1>"
        '<p class="note">It may have been retired, or it may never have been '
        "one of ours. Either way there is nothing here to see, and nothing "
        "you need to do.</p></div>"))


def _rows(card: dict) -> str:
    progs = card.get("programs") or []
    out = [
        f'<div class="row"><span>State</span>'
        f'<span>{html.escape(card.get("state") or "—")}</span></div>',
    ]
    if progs:
        chips = "".join(f'<span class="prog">{html.escape(p.upper())}</span>'
                        for p in progs)
        out.append(f'<div class="row"><span>Governed by</span>'
                   f'<span class="progs">{chips}</span></div>')
    if card.get("held_by"):
        out.append(f'<div class="row"><span>Held by</span>'
                   f'<span>{html.escape(card["held_by"])}</span></div>')
    return "".join(out)


_FOUND_JS = """
(function(){
 var f=document.getElementById('f'),b=document.getElementById('go'),
     s=document.getElementById('st');
 if(!f)return;
 f.addEventListener('submit',function(e){
  e.preventDefault();b.disabled=true;s.textContent='Recording\\u2026';
  fetch(%(endpoint)s,{method:'POST',
   headers:{'content-type':'application/json'},
   body:JSON.stringify({where:document.getElementById('w').value||null,
                        contact:document.getElementById('c').value||null})})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
  .then(function(o){
   if(o.ok){b.remove();s.textContent=o.j.note||'Recorded. Thank you.';}
   else{b.disabled=false;s.textContent=(o.j&&o.j.detail)||'That did not go through.';}
  }).catch(function(){b.disabled=false;
   s.textContent='No connection \\u2014 try again in a moment.';});
 });
})();
"""

_RING_JS = """
(function(){
 var f=document.getElementById('f'),b=document.getElementById('go'),
     s=document.getElementById('st');
 if(!f)return;
 f.addEventListener('submit',function(e){
  e.preventDefault();b.disabled=true;s.textContent='Ringing\\u2026';
  fetch(%(endpoint)s,{method:'POST',
   headers:{'content-type':'application/json'},
   body:JSON.stringify({kind:document.getElementById('k').value,
                        note:document.getElementById('n').value||null})})
  .then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});})
  .then(function(o){
   if(o.ok){f.innerHTML='';
    var w=document.createElement('div');w.className='seal';
    w.innerHTML='<div class="badge">'+(o.j.ai_generated?'AI REPLY':'AUTOMATED')
     +'</div><h1>'+esc(o.j.words||'')+'</h1>'
     +'<p class="note">'+esc(o.j.disclosure||'')+'</p>'
     +(o.j.handed_to?'<div class="row"><span>Passed to</span><span>'
       +esc(o.j.handed_to)+'</span></div>':'');
    f.parentNode.appendChild(w);s.textContent='';}
   else{b.disabled=false;s.textContent=(o.j&&o.j.detail)||'That did not go through.';}
  }).catch(function(){b.disabled=false;
   s.textContent='No connection \\u2014 try again in a moment.';});
 });
 function esc(t){var d=document.createElement('div');d.textContent=t;
  return d.innerHTML;}
})();
"""


def seal_card_page(card: dict) -> str:
    """A carrier: what it is, what governs it, and how to hand it in.

    Renders only what ``beacons.seal_card`` returned. There is no second
    lookup here and nothing is fetched to decorate it, so this page cannot
    disclose something the card itself withheld.
    """
    ref = html.escape(card["reference"])
    held = card.get("held_by")
    who = (f"This belongs to {html.escape(held)}." if held else
           "Report it here and the holder will be told — you won't learn "
           "whose it is, and you don't need to.")
    body = (
        '<div class="seal">'
        f'<div class="badge">{html.escape(card["badge"])}</div>'
        "<h1>This is under custody</h1>"
        f'<p class="ref">{ref}</p>'
        f"{_rows(card)}"
        f'<p class="note">{who}</p>'
        '<div class="never">This code cannot open it, and neither can '
        "whoever is holding it. It says the thing is sealed — never what is "
        "inside.</div>"
        '<form id="f">'
        '<label for="w">Where is it?</label>'
        '<input id="w" name="w" autocomplete="off" '
        'placeholder="depot 3, Oakland">'
        '<label for="c">How can you be reached? (optional)</label>'
        '<input id="c" name="c" autocomplete="off" placeholder="name, phone">'
        '<button id="go" type="submit">I found this</button>'
        "</form>"
        '<div class="status" id="st"></div>'
        "</div>"
        '<p class="foot">Your report is timestamped and hash-chained into '
        "this carrier's chain of custody. It cannot be altered afterwards — "
        "including by us.</p>"
        "<script>"
        + _FOUND_JS % {"endpoint": _js(f"/s/{card['reference']}/found")}
        + "</script>")
    return _page("Sealed carrier", body)


def gate_page(card: dict) -> str:
    """A facility gate: ring it, and see what answers.

    The reply renders in place rather than as a new page, because somebody
    standing at a door in the rain should not have to watch a navigation.
    """
    ref = html.escape(card["reference"])
    body = (
        '<div class="seal">'
        f'<div class="badge">{html.escape(card["badge"])}</div>'
        "<h1>Controlled facility</h1>"
        f'<p class="ref">{ref}</p>'
        f"{_rows(card)}"
        f'<p class="note">{html.escape(card.get("note") or "")}</p>'
        '<form id="f">'
        '<label for="k">What are you here for?</label>'
        '<select id="k" name="k">'
        '<option value="delivery">A delivery</option>'
        '<option value="collection">A collection</option>'
        '<option value="access">Access to the site</option>'
        '<option value="other">Something else</option>'
        "</select>"
        '<label for="n">Anything else we should know?</label>'
        '<textarea id="n" name="n" rows="3" '
        'placeholder="who you are, who you were expecting to meet"></textarea>'
        '<button id="go" type="submit">Ring</button>'
        "</form>"
        '<div class="status" id="st"></div>'
        "</div>"
        '<p class="foot">Whoever answers cannot let anyone in — that decision '
        "always belongs to a person. This exchange is recorded in the "
        "facility's audit chain.</p>"
        "<script>"
        + _RING_JS % {"endpoint": _js(f"/s/{card['reference']}/ring")}
        + "</script>")
    return _page("Controlled facility", body)


def page_for(card: dict) -> str:
    """The right page for whatever the code was placed on."""
    return gate_page(card) if card.get("gate") else seal_card_page(card)
