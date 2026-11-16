// Renders the Outcrop introduction video frames from the clean design preview (sample content only).
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const S = process.argv[2]; const OUT = path.join(S, 'video', 'frames');
fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
const FPS = 30;
let n = 0;
// MIN: minimum seconds per scene (opening card, 11 screens, closing card), to fit the narration.
const MIN = JSON.parse(process.env.MIN || '[]'); const STARTS = [];
// CAPS: subtitles of the narration, [{t0, t1, text}] in seconds.
const CAPS = process.env.CAPS ? JSON.parse(fs.readFileSync(process.env.CAPS, 'utf8')) : null;
const capAt = (t) => { const c = CAPS && CAPS.find((c) => t >= c.t0 && t < c.t1); return c ? c.text : ''; };
const lastFrame = () => path.join(OUT, String(n - 1).padStart(5, '0') + '.png');
const frame = () => path.join(OUT, String(n++).padStart(5, '0') + '.png');

const SCENES = [
  { tour: 0, cap: 'Outcrop keeps your work in one private record.', scroll: 210, hold: 3.2, holdEnd: 2.8 },
  { nav: ['uncover', null], cap: 'Begin wherever is easiest: your résumé, an experience from it, or a piece of work you remember.', scroll: 0, hold: 3.5 },
  { nav: ['resume', 'populated'], cap: 'Start from your résumé: review what Outcrop found, then add it all to your record.', scroll: 240 },
  { nav: ['resume-continue', null], cap: 'Explore an experience from your résumé: pick one and uncover what it involved.', scroll: 0, hold: 3.5 },
  { tour: 2, cap: 'Or tell Outcrop about a piece of work you remember.', scroll: 0, hold: 3 },
  { tour: 3, cap: 'Outcrop asks focused questions and reflects back what it understood, in your words.', scroll: 260 },
  { tour: 4, cap: 'When it’s ready, review the Evidence draft. Nothing joins your record until you save it.', text: 'Before you save', offset: 40, hold: 2.2, dur: 4.2, holdEnd: 3.2, capEnd: 'Before you save, confirm when it happened and the tools you used.' },
  { tour: 6, cap: 'Your Landscape shows what your saved Evidence supports. No scores.', scroll: 0, top: true },
  { tour: 7, cap: 'Every reading is tied to your own words.', scroll: 420 },
  { tour: 9, cap: 'Check a job against your record: what it supports, and what isn’t in it yet.', el: '.compare:not(.reading)', hold: 0.8, dur: 8, holdEnd: 1.8 },
  { career: true, cap: 'Your career, in one place, ready to use when an opportunity appears.', scroll: 0 },
];

const CARD_CSS = `#vx-card{position:fixed;inset:0;z-index:200;background:#f3efe4;display:grid;place-items:center;text-align:center}
#vx-card .m{display:flex;align-items:center;gap:18px;justify-content:center}
#vx-card .m span{font-family:"Cormorant Garamond",serif;font-size:72px;font-weight:500;color:#242720}
#vx-card .m svg{width:70px}
#vx-card h1{font-family:"Cormorant Garamond",serif;font-weight:500;font-size:44px;color:#242720;margin:18px 0 0}
#vx-card p{font-family:"Montserrat",sans-serif;font-size:18px;color:#5b6157;margin:22px 0 0}
#vx-cap{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:250;max-width:780px;width:max-content;background:rgba(36,39,32,.78);color:#f3efe4;border-radius:10px;padding:7px 16px;font-family:"Source Serif 4",serif;font-size:19px;line-height:1.35;text-align:center}
#vx-cap:empty{display:none}
#vx-tags{position:fixed;top:16px;right:20px;z-index:150;display:flex;gap:8px}
#vx-tags span{font-family:"Montserrat",sans-serif;font-size:13px;font-weight:600;border-radius:999px;padding:5px 12px;background:#f3efe4;border:1px solid rgba(36,39,32,.28);color:#242720}
#vx-tags .dev{background:#a5753c;border-color:#a5753c;color:#f3efe4}
[hidden]{display:none!important} #pv-bar,#pv-label{display:none!important} *:focus{outline:none!important}`;
const LOGO = '<svg viewBox="0 0 30 22"><rect x="9" y="1" width="12" height="5" rx="2" fill="#a5753c"/><rect x="5" y="8.5" width="20" height="5" rx="2" fill="#59634b"/><rect x="1" y="16" width="28" height="5" rx="2" fill="#4b5440"/></svg>';

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await p.route(/fonts\.googleapis\.com.*/, (r) => r.fulfill({ contentType: 'text/css', body: fs.readFileSync(S + '/fonts.css', 'utf8') }));
  await p.goto('file://' + S + '/'+(process.env.PREVIEW||'preview.html'));
  await p.addStyleTag({ content: CARD_CSS });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  let shown = null, last = null;
  const syncCap = async () => {
    if (!CAPS) return false;
    const want = capAt(n / FPS); if (want === shown) return false;
    await p.evaluate((t) => { let c = document.getElementById('vx-cap'); if (!c) { c = document.createElement('div'); c.id = 'vx-cap'; document.body.appendChild(c); } c.textContent = t; }, want);
    shown = want; return true;
  };
  const shot = async () => { await syncCap(); const f = frame(); await p.screenshot({ path: f }); last = f; return f; };
  // A held frame is re-shot only when the subtitle changes; otherwise it is linked.
  const extend = async (count) => { for (let i = 0; i < count; i++) { if (await syncCap() || !last) await shot(); else fs.linkSync(last, frame()); } };
  const hold = async (sec) => { await shot(); await extend(Math.ceil(sec * FPS) - 1); };
  const pad = async (start, i) => { const want = Math.round((MIN[i] || 0) * FPS); if (n - start < want) await extend(want - (n - start)); };
  const card = async (html, sec, fit) => {
    await p.evaluate((h) => { let c = document.getElementById('vx-card'); if (!c) { c = document.createElement('div'); c.id = 'vx-card'; document.body.appendChild(c); } c.innerHTML = h; c.hidden = false; }, html);
    await p.waitForTimeout(200); await hold(sec);
    if (fit) await fit(); // stretch to the narration while the card is still showing
    await p.evaluate(() => { document.getElementById('vx-card').hidden = true; });
  };
  const overlay = async (cap, dev) => {
    await p.evaluate(([cap, dev]) => {
      let c = document.getElementById('vx-cap'); if (!c) { c = document.createElement('div'); c.id = 'vx-cap'; document.body.appendChild(c); }
      if (cap !== null) c.textContent = cap;
      let t = document.getElementById('vx-tags'); if (!t) { t = document.createElement('div'); t.id = 'vx-tags'; document.body.appendChild(t); }
      t.innerHTML = '<span>Sample content</span>' + (dev ? '<span class="dev">In development</span>' : '');
      if (document.activeElement) document.activeElement.blur();
    }, [CAPS ? null : cap, !!dev]);
  };

  STARTS.push(n); await card(`<div><div class="m">${LOGO}<span>Outcrop</span></div><h1>Your work, in your words.</h1></div>`, 3, () => pad(STARTS[0], 0));

  await p.evaluate(() => document.querySelector('[data-pv="tour"]').click());
  let cur = 0;
  for (const [k, sc] of SCENES.entries()) {
    const st = n; STARTS.push(st);
    if (sc.career) {
      for (let i = cur; i < 13; i++) await p.evaluate(() => document.getElementById('pv-next').click());
      await p.evaluate(() => document.querySelector('[data-nav="record"]').click()); await p.waitForTimeout(200);
      await p.evaluate(() => { const e = [...document.querySelectorAll('a,button')].find((e) => /Career record/.test(e.textContent)); e && e.click(); });
    } else if (sc.nav) {
      await p.evaluate(([v, st]) => { const a = document.createElement('a'); a.href = '#' + v; a.dataset.nav = v; if (st) a.dataset.state = st; document.body.appendChild(a); a.click(); a.remove(); }, sc.nav);
    } else {
      while (cur < sc.tour) { await p.evaluate(() => document.getElementById('pv-next').click()); cur++; await p.waitForTimeout(60); }
    }
    await p.waitForTimeout(500);
    if (sc.top) await p.evaluate(() => scrollTo(0, 0));
    else await p.evaluate(() => scrollTo(0, 0));
    await overlay(sc.cap, sc.dev);
    await p.waitForTimeout(150);
    await hold(sc.hold || (sc.scroll ? 2.2 : 5.5));
    if (sc.text) sc.scroll = await p.evaluate(([t, off]) => { const e = [...document.querySelectorAll('h1,h2,h3,h4,p,legend')].find((e) => e.textContent.trim().startsWith(t)); return e ? Math.round(e.getBoundingClientRect().top + scrollY - off) : 400; }, [sc.text, sc.offset || 60]);
    if (sc.el) sc.scroll = await p.evaluate((q) => { const e = document.querySelector(q); return e ? Math.round(e.getBoundingClientRect().top + scrollY - 70) : 300; }, sc.el);
    if (sc.scroll) {
      const max = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
      const to = Math.min(sc.scroll, Math.max(0, max));
      const steps = Math.round((sc.dur || 2.6) * FPS);
      for (let i = 1; i <= steps; i++) {
        const t = i / steps; const e = t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        await p.evaluate((y) => scrollTo(0, y), Math.round(to * e));
        await shot();
      }
      if (sc.capEnd) { await overlay(sc.capEnd, sc.dev); await p.waitForTimeout(100); }
      await hold(sc.holdEnd || 1.8);
    }
    await pad(st, k + 1);
  }
  await p.evaluate((ids) => { for (const id of ids) { const e = document.getElementById(id); if (e) e.remove(); } }, CAPS ? ['vx-tags'] : ['vx-cap', 'vx-tags']);
  STARTS.push(n); const cs = n;
  await card(`<div><div class="m">${LOGO}<span>Outcrop</span></div><h1>Recognize, preserve and use the value of your work.</h1><p>outcrop.me · Request early access</p></div>`, 4, () => pad(cs, SCENES.length + 1));
  fs.writeFileSync(path.join(S, 'video', 'starts.json'), JSON.stringify(STARTS.map((f) => f / FPS)));
  await b.close();
  console.log('frames', n, 'seconds', (n / FPS).toFixed(1));
})();
