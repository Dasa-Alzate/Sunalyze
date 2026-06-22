# Landing update + legal pages — research & plan

## Goal
1. Communicate new product capabilities on the marketing landing.
2. Resolve 3 `jsx-a11y/anchor-is-valid` warnings (Landing footer, Auth legal links) by
   creating real legal pages and pointing the anchors at navigable routes.

## Findings (current state)
- `features/marketing/Landing.jsx`: data-driven `FEATURES` array (icon/title/desc),
  rendered into `.web-feature` cards. Footer columns are data-driven; items are plain
  strings rendered as `<a href="#" onClick={preventDefault}>` (the warning at ~line 294).
- Navigation: `useTransition().navigate(path)`. Landing's `go(key)` maps keys to paths.
  `TransitionLink` component already exists (`to` -> animated navigate, real `href`).
- Router: `createBrowserRouter`, public routes live as children of `RootLayout`
  (`/`, `/login`, `/signup`, ...). `RootLayout` provides Transition/Auth/Command context.
- `Auth.jsx` line 119: `auth-legal` paragraph has two `<a href="#">` (Condiciones,
  Política de privacidad) -> 2 warnings.
- Design system: `web.css` exposes `.web`, `.web-wrap`, `.web-section`, `.web-eyebrow`,
  `.web-h2`, `.web-lead`, `.web-footer*`. Skip-link class `sun-skip-link`.
- Tests: vitest + vitest-axe; pattern `axe(container, { rules: { 'color-contrast': off }})`.
- GDPR already implemented (see docs/gdpr-research.md, compliance-gdpr.md): export +
  right to erasure, AuditEvent log, MFA on privileged access. Legal copy must be coherent.

## Plan
### Part 1 — Features copy
- Extend `FEATURES` array with the new capabilities (templates, finance/savings study,
  batteries, EU compliance, marketplace+flags, power-user, AA accessibility). Keep the
  existing card structure/tone. Truthful: present flag-gated ones as available modules.
- Add a dedicated "Compliance / EU" trust strip is optional; minimal approach is to keep
  one Features grid + a short compliance line, reusing existing classes. Add a compact
  "Cumplimiento y módulos" section reusing `.web-section`/`.web-feature` if it reads better.

### Part 2 — Legal pages
- New `features/legal/Legal.jsx` exporting `PrivacyPolicy`, `Terms`, `Cookies`.
  Shared `LegalShell` with `.web` wrapper, nav brand back to landing, skip-link,
  single `<h1>`, `<main id="main">`, footer-consistent styling. Reuse `web.css` classes;
  add minimal `.web-legal` prose styles if needed.
- Routes: `/legal/privacidad`, `/legal/terminos`, `/legal/cookies`.
- Footer items become `{ label, to }` objects; legal items link to routes via
  `navigate`/real href; section anchors (`#features`, etc.) stay as in-page anchors.
- Auth.jsx legal links point to `/legal/terminos` and `/legal/privacidad` (real hrefs).

### Verify
- `npm run build && npx eslint src && npm test` -> 0 errors, 0 warnings.
- Add `src/test/legal.test.jsx` axe test for the 3 legal pages.
