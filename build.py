"""Build outcrop.me from src/: the deployable static site (site/) and a private review preview (preview/outcrop-site-preview.html)."""
import base64, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).parent
SRC, ASSETS = ROOT / "src", ROOT / "assets"
SITE, PREVIEW = ROOT / "site", ROOT / "preview"

LOGO = ('<svg viewBox="0 0 30 22" role="img" aria-hidden="true" focusable="false">'
        '<rect x="9" y="1" width="12" height="5" rx="2" fill="#a5753c"/>'
        '<rect x="5" y="8.5" width="20" height="5" rx="2" fill="#59634b"/>'
        '<rect x="1" y="16" width="28" height="5" rx="2" fill="#4b5440"/></svg>')
TITLE = "Outcrop"
DESCRIPTION = ("Upload your résumé, check a job against your record, uncover the work stories behind it. "
               "Outcrop surfaces the capabilities they demonstrate. The feedback you never got, from your own record.")

body = (SRC / "body.html").read_text()
method = (SRC / "methodology.html").read_text()
METHOD_DESCRIPTION = ("How Outcrop reads your work: every capability is tied to your own words and checked against written rules. "
                      "No scores, no guessing, and the limits stated plainly.")
css = (SRC / "site.css").read_text()
FONTS = [("Cormorant Garamond", 500, "normal", "cormorant-garamond-latin-500-normal.woff2"),
         ("Cormorant Garamond", 600, "normal", "cormorant-garamond-latin-600-normal.woff2"),
         ("Montserrat", 500, "normal", "montserrat-latin-500-normal.woff2"),
         ("Montserrat", 600, "normal", "montserrat-latin-600-normal.woff2"),
         ("Source Serif 4", 400, "normal", "source-serif-4-latin-400-normal.woff2"),
         ("Source Serif 4", 400, "italic", "source-serif-4-latin-400-italic.woff2"),
         ("Source Serif 4", 600, "normal", "source-serif-4-latin-600-normal.woff2")]

CFG = json.loads((ROOT / "config.js").read_text().split("=", 1)[1].strip().rstrip(";"))
SIGNIN_ON = CFG.get("signInEnabled", True)

def fill(html, img, signin, early, note, video, method="methodology/", home=""):
    if not SIGNIN_ON:  # the app is not open yet (config.js signInEnabled): Sign in becomes Request early access
        html = re.sub(r'\s*<a [^>]*href="[^"]*#early-access"[^>]*>Early access</a>', '', html)          # avoid a duplicate link
        html = re.sub(r'<a href="\{\{SIGNIN\}\}" data-signin>Sign in</a>', '<a href="{{EARLY}}" data-early>Request early access</a>', html)
        html = re.sub(r'\s*<a [^>]*data-signin[^>]*>.*?</a>', '', html, flags=re.S)
    html = html.replace("{{METHOD}}", method).replace("{{HOME}}", home)
    html = html.replace("{{LOGO}}", LOGO).replace("{{SIGNIN}}", signin).replace("{{EARLY}}", early).replace("{{CONFIGNOTE}}", note)
    for name in ["today-phone", "resume-review", "conversation", "evidence-draft", "capabilities", "job-check", "career-record", "your-record"]:
        html = html.replace("{{IMG:%s}}" % name, img(name))
    html = html.replace("{{VIDEO}}", video("outcrop-introduction.mp4")).replace("{{POSTER}}", video("poster.webp"))
    assert "{{" not in html, "unfilled placeholder"
    return html

# ---------- deployable site ----------
if SITE.exists(): shutil.rmtree(SITE)
(SITE / "assets").mkdir(parents=True)
shutil.copytree(ASSETS / "fonts", SITE / "assets" / "fonts")
shutil.copytree(ASSETS / "img", SITE / "assets" / "img", ignore=shutil.ignore_patterns("*.jpg"))
shutil.copy(ROOT / "config.js", SITE / "assets" / "config.js")
fontcss = "".join(
    f'@font-face{{font-family:"{f}";font-weight:{w};font-style:{s};font-display:swap;src:url(fonts/{file}) format("woff2")}}\n'
    for f, w, s, file in FONTS)
(SITE / "assets" / "site.css").write_text(fontcss + css)
(SITE / "assets" / "site.js").write_text("""// Every product link comes from assets/config.js (one value: appOrigin).
(function () {
  var c = window.OUTCROP_SITE || {};
  var early = document.querySelectorAll('[data-early]');
  for (var i = 0; i < early.length; i++) { if (c.earlyAccessUrl) early[i].href = c.earlyAccessUrl; }
})();
""")
favicon = LOGO.replace('aria-hidden="true" focusable="false"', 'xmlns="http://www.w3.org/2000/svg"')
(SITE / "assets" / "logo.svg").write_text(favicon)
shutil.copytree(ASSETS / "video", SITE / "assets" / "video")
EARLY = CFG.get("earlyAccessUrl") or "#early-access"
site_body = fill(body, lambda n: f"assets/img/{n}.webp", "/sign-in", EARLY, "", lambda f: f"assets/video/{f}")
(SITE / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<meta property="og:title" content="Outcrop">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://outcrop.me/">
<meta property="og:image" content="https://outcrop.me/assets/img/landscape.webp">
<link rel="icon" href="assets/logo.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/cormorant-garamond-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/site.css">
<script src="assets/config.js"></script>
<script src="assets/site.js" defer></script>
</head>
<body>
{site_body}
</body>
</html>
""")
if SIGNIN_ON:
  (SITE / "sign-in").mkdir()
  (SITE / "sign-in" / "index.html").write_text("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Sign in · Outcrop</title>
<script src="../assets/config.js"></script>
<script>
  // outcrop.me/sign-in always opens the product's sign-in. The address lives only in assets/config.js.
  (function () { var c = window.OUTCROP_SITE || {}; if (c.appOrigin) location.replace(c.appOrigin + (c.signInPath || '/')); })();
</script>
<style>body{margin:0;background:#f3efe4;color:#242720;font:17px/1.6 Georgia,serif;display:grid;place-items:center;min-height:100vh;padding:24px;box-sizing:border-box}</style>
</head>
<body>
<p>Opening Outcrop sign-in…</p>
<noscript><p>Sign-in needs JavaScript in this browser.</p></noscript>
</body>
</html>
""")
(SITE / "methodology").mkdir()
method_body = fill(method, lambda n: "", "/sign-in", CFG.get("earlyAccessUrl") or "../#early-access", "", lambda f: "", method="./", home="../")
(SITE / "methodology" / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>The method · Outcrop</title>
<meta name="description" content="{METHOD_DESCRIPTION}">
<meta property="og:title" content="Not a black box · Outcrop">
<meta property="og:description" content="{METHOD_DESCRIPTION}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://outcrop.me/methodology/">
<link rel="icon" href="../assets/logo.svg" type="image/svg+xml">
<link rel="preload" href="../assets/fonts/cormorant-garamond-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../assets/site.css">
<script src="../assets/config.js"></script>
<script src="../assets/site.js" defer></script>
</head>
<body>
{method_body}
</body>
</html>
""")
(SITE / "robots.txt").write_text("User-agent: *\nAllow: /\n")
# GitHub Pages: the custom domain, and no Jekyll processing.
(SITE / "CNAME").write_text("outcrop.me\n")
(SITE / ".nojekyll").write_text("")
(SITE / "404.html").write_text("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Not found · Outcrop</title><link rel="icon" href="/assets/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"></head>
<body><main class="wrap" style="min-height:70vh;display:grid;place-content:center;gap:16px;text-align:center">
<h1>This page isn’t here.</h1><p><a class="btn primary" href="/">Go to Outcrop</a></p></main></body></html>
""")

# ---------- private review preview (Artifact) ----------
PREVIEW.mkdir(exist_ok=True)
def data_uri(name):
    return "data:image/webp;base64," + base64.b64encode((ASSETS / "img" / f"{name}.webp").read_bytes()).decode()
cfg = json.loads((ROOT / "config.js").read_text().split("=", 1)[1].strip().rstrip(";"))
note = ('<p class="config-note">Preview only: the early-access destination is not connected yet'
        + (', and Sign in goes to ' + cfg["appOrigin"] + cfg["signInPath"] if SIGNIN_ON else ', and Sign in is hidden until the app opens') + '.</p>')
def video_uri(f):
    mime = "video/mp4" if f.endswith(".mp4") else "image/webp"
    return f"data:{mime};base64," + base64.b64encode((ASSETS / "video" / f).read_bytes()).decode()
prev_home = fill(body, data_uri, cfg["appOrigin"] + cfg["signInPath"], EARLY, "" if CFG.get("earlyAccessUrl") else note, video_uri, method="#methodology")
prev_method = fill(method, data_uri, cfg["appOrigin"] + cfg["signInPath"], EARLY, "", video_uri, method="#methodology", home="")
prev_body = (f'<div data-page="home">\n{prev_home}\n</div>\n<div data-page="method" hidden>\n{prev_method}\n</div>\n'
             '<script>\n// Preview only: both pages in one file. #methodology shows the method page; any other link shows the home page.\n'
             '(function () {\n  function show() {\n    var m = location.hash === "#methodology";\n'
             '    document.querySelector("[data-page=home]").hidden = m;\n    document.querySelector("[data-page=method]").hidden = !m;\n'
             '    if (m) window.scrollTo(0, 0); else if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }\n  }\n'
             '  window.addEventListener("hashchange", show); show();\n})();\n</script>')
gfonts = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600'
          '&family=Montserrat:wght@500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">')
(PREVIEW / "outcrop-site-preview.html").write_text(
    f'<title>outcrop.me preview</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{gfonts}\n<style>\n{css}</style>\n{prev_body}\n')
print("built", sum(1 for _ in SITE.rglob("*") if _.is_file()), "site files;",
      round((PREVIEW / "outcrop-site-preview.html").stat().st_size / 1024), "KB preview")
