# EPIC: Improve the UI footer

> Golden thread: follows `modernise-user-interface` (archived; it built the job console and left
> the footer as one line). Capability: `job-console`. Seed: `inputs/seed.md` (the developer,
> 2026-11-14).

## Appetite

**SMALL**. One template, the stylesheet, two icons and one value passed to the templates. No new
page, no new setting, no JavaScript.

## Why

The footer says "Powered by Meaningfy" and links to the GitHub organisation. A user cannot tell
from the UI which version runs, under which licence, or where the source and the issue tracker
are; and the tool does not show who made it the way Meaningfy wants to.

## Solution outline

When this is done, every page of the UI ends with one row:

```
 Made with ♥ by [Meaningfy logo]            GitHub · Apache-2.0 · v0.1.0
```

The credit reads "Made with love by Meaningfy": a red heart at text size that pulses slowly, and
the Meaningfy logo linking to the company website. Beside it are a link to this repository, the
licence linking to the `LICENSE` file, and the version of the installed package. On a narrow
screen the row becomes two centred lines. It reads well on the light and the dark theme, and to a
screen reader.

**Success measure**: the feature scenarios pass for the jobs list, the new-job page, the report
viewer and the error page: the footer is present, its three links point to the Meaningfy website,
the repository and the licence, and the version shown equals the installed package version; a unit
test pins that the stylesheet stops the pulse under `prefers-reduced-motion`.

## Key decisions

- **DEC-1 One row.** Credit on one side; links, licence and version on the other. Rejected: a
  multi-column footer (a company-website pattern, too heavy for three links).
- **DEC-2 No terms page.** The licence name links to `LICENSE` in the repository. Rejected: a
  `/terms` page (the developer: the licence is enough).
- **DEC-3 The logo takes the text colour.** The logo (`inputs/meaningfy-logo.svg`, mark and
  wordmark) is inlined at text height and inherits the footer's colour, so it reads on both themes.
  Rejected: brand navy `#212c4a` (unreadable on the dark theme); an image file (cannot follow the
  theme).
- **DEC-4 The heart.** Red (the stylesheet's existing danger colour), text size, pulsing through
  CSS only; still under `prefers-reduced-motion`; hidden from screen readers, which hear "Made with
  love by Meaningfy". Rejected: an emoji (its colour and shape vary by platform); a JavaScript
  animation.
- **DEC-5 Links.** The Meaningfy website (`https://meaningfy.lu`), this repository (`https://github.com/meaningfy-ws/rdf-fingerprinter-ws`) and the
  licence (`LICENSE` on the repository's `main` branch, the released one). External links carry
  `rel="noopener"`. Rejected for now: Docs (not published) and API
  (the UI knows no address a browser can reach).
- **DEC-6 The version is read, not written.** The footer shows the installed package version.
  Rejected: a version written in the template (it would go stale at the first release).
- **DEC-7 Risks accepted** (the developer, 2026-11-14; table in `inputs/seed.md`): the version is
  visible to anyone who can open the UI (RISK-1); the logo file becomes public in an Apache-2.0
  repository (RISK-2); an instance run by someone else shows "by Meaningfy" (RISK-3); the logo may
  change (RISK-4).

## Rabbit-holes

- **Redrawing the logo.** Use the two paths as they are; do not simplify or re-trace them.
- **Theme-specific colours.** No per-theme logo variants; DEC-3 settles it.
- **Operator branding.** Whoever runs an instance cannot change the footer; no settings for it.
- **Legibility at text height.** If the wordmark is unreadable at the footer's size, raise the
  logo's height a little; do not swap in the mark alone without asking the developer.

## No-gos

- A terms, privacy or imprint page.
- Docs and API links, and any new setting for a public address.
- Social links, a newsletter, a cookie banner, a copyright line, a "report an issue" link.
- Any change to the header, the navigation or other pages' content.
- JavaScript for the footer.

---

## What Changes

- The footer in `base.html` is replaced by the row of the solution outline.
- `icons.html` gains the heart and the Meaningfy logo.
- `app.css` gains the footer layout, the pulse and its `prefers-reduced-motion` rule.
- The UI passes the installed package version to every template.
- The images install the package instead of copying its folder.
- `job-console` gains one requirement, with its feature scenarios.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `job-console`: adds the requirement "Every page ends with the footer" (credit, links, licence,
  version, accessibility, reduced motion).

## Impact

- Code: `fingerprinter/entrypoints/ui/` only (`templates/base.html`, `templates/icons.html`,
  `static/app.css`, the app factory). No layer boundary moves.
- Tests: UI unit tests and a `job-console` feature.
- Infrastructure: `infra/docker/Dockerfile` installs the package, so that the images know their
  version (amended 2026-11-14, the developer's answer at the PLAN; `design.md` F-2). The line read
  "no infrastructure change" when the EPIC was shaped.
- No API, dependency or library change. `rdf-fingerprinter` is not involved.
