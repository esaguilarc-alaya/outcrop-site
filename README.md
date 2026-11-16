# outcrop.me — marketing site

A one-page editorial site for Outcrop. The product itself lives at `app.outcrop.me`; this site only explains Outcrop and sends people to sign in or request early access.

## Layout

```text
src/body.html      page content (one source for the site and the review preview)
src/site.css       styles (Outcrop palette and faces)
assets/fonts/      self-hosted fonts (Cormorant Garamond, Montserrat, Source Serif 4; SIL Open Font License)
assets/img/        product screenshots from the clean Outcrop preview, sample content only
assets/video/      the introduction video and its poster frame
config.js          the ONLY place that names the product address and the early-access destination
build.py           builds site/ (deployable) and preview/ (private review page)
site/              the built static site: deploy this folder as-is
```

Rebuild after any change: `python3 build.py`.

## One configuration value

`config.js`:

```js
window.OUTCROP_SITE = {"appOrigin": "https://app.outcrop.me", "signInPath": "/login", "signInEnabled": false, "earlyAccessUrl": "mailto:curious@alayacrafts.com?subject=Early%20access%20to%20Outcrop"};
```

- `signInEnabled` is `false` while the app is closed: every Sign in link becomes Request early access, the separate Early access link is dropped, and there is no `/sign-in` page. Set it to `true` and rebuild when `app.outcrop.me` answers.
- With Sign in on, every Sign in link goes to `/sign-in`, which forwards to `appOrigin + signInPath`.
- `earlyAccessUrl`: where every Request early access link goes. Now an email to curious@alayacrafts.com with the subject "Early access to Outcrop". If it is empty, the buttons scroll to the early-access section.

## Publishing (GitHub Pages, custom domain outcrop.me)

1. `python3 build.py` — rebuilds `site/`, including `CNAME` (outcrop.me), `.nojekyll` and `404.html`.
2. Commit and push to `main`. `.github/workflows/pages.yml` publishes `site/` as committed.
3. Repository settings → Pages → Source: GitHub Actions. Custom domain: outcrop.me. Enforce HTTPS once the certificate is issued.
4. DNS (Cloudflare), DNS only (grey cloud) so GitHub can issue the certificate:
   - `A  outcrop.me  185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME  www  esaguilarc-alaya.github.io`

## Before going public

- Steve reviews the page once (marketing copy rule, 2026-10-26): correct only wording that is inaccurate, unclear or promises more than Outcrop delivers.
- Turn `signInEnabled` on only when `app.outcrop.me` answers.
- The one-minute introduction (`assets/video/outcrop-introduction.mp4`, narrated by Steve, captions in the picture) is rendered from the clean Outcrop preview. "See how Outcrop works" opens it in a dialog and starts it only on that click; it never plays on page load, and Sign in never opens it. To re-render it after the design changes, re-render it with `tools/make-intro-video.js` (Playwright over the clean preview, then ffmpeg) and copy the MP4 into `assets/video/`. The narration is placed line by line on its scenes; each scene lasts at least as long as its line.
