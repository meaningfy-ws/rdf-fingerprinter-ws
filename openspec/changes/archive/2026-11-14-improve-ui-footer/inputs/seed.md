# Seed (developer, 2026-11-14)

Secondary record of the shaping session; the EPIC (`../proposal.md`) supersedes it. Never groomed.

## What the developer said

> i want to brainstorm about better footer in the ui

> I want in the footer to say made with love by Meaningfy (with Meaningfy logo), and put an animated
> pulsing heart (text zise icon in red), then we also want simple terms page , and links to the
> github repo, to meaingfy website etc. propose what would be an adequate footer for an open source
> gig tool like this one

> okay lets skip terms (stick to what is in licence maybe, that is god enough), lookup an
> appropriate mennigfy logo, I theink we had some on gDrive markeing in common space otehrwise okay,

> yes I approve , proceed

## What was found

- Today's footer: one line, "Powered by Meaningfy" linking to the GitHub organisation
  (`fingerprinter/entrypoints/ui/templates/base.html`, `.site-footer` in `static/app.css`). No
  requirement in `openspec/specs/` mentions it.
- Logo: `Meaningfy_Blue.svg` on Google Drive (modified 2026-05-22), the mark and the wordmark in
  navy `#212c4a`, two paths. Kept here as `meaningfy-logo.svg`. Same artwork as "Blue logo - no
  background.svg" in the Common space.
- The UI follows the system colour scheme; navy is unreadable on the dark theme.
- The docs are not published (the repository has no GitHub Pages site).
- The UI knows only the API's internal address (`Settings.api_url`), not one a browser can reach.
- Version `0.1.0` and licence Apache-2.0 are in `pyproject.toml`; `LICENSE` is at the repo root.

## Questions and answers

| Question | Answer |
|---|---|
| What should the footer say? | "Made with love by Meaningfy", with the logo and a red pulsing heart at text size (developer). |
| A terms page? | No. The licence is enough; link to it (developer). |
| Which links? | The GitHub repository and the Meaningfy website (developer). Docs and API links proposed, then dropped: no address to link to (agent's call, approved). |
| Which logo? | The newest on Drive, full logo (mark and wordmark) at text height, taking the text colour so it reads on both themes (agent's call, approved). |
| Show the version? | Yes, the installed package version (agent's proposal, approved). |
| Layout? | One row; two centred lines on a phone. No JavaScript (agent's call, approved). |

## Approaches considered

1. **One row** (chosen): credit on the left, links, licence and version on the right. Fits a
   single-purpose console.
2. **Multi-column footer** with link groups: suits a company website; too heavy for three links.
3. **Footer plus a terms page**: dropped by the developer; the licence covers it.

## What it must prove (approved)

1. Every page shows the footer: jobs list, new job, report viewer, error page.
2. The links point to the Meaningfy website, the repository and the licence.
3. The version shown equals the installed package version.
4. The heart is hidden from screen readers; the sentence reads "Made with love by Meaningfy".
5. The stylesheet stops the pulse under `prefers-reduced-motion`.

It fails if the version is hard-coded, an external link lacks `rel="noopener"`, or the animation
needs JavaScript.

## Risks (all accepted by the developer)

| Id | Risk | Likelihood, impact | Answer |
|---|---|---|---|
| RISK-1 | The version is visible to anyone who can open the UI | Low, low: the code is public; the UI is published on loopback | Accept |
| RISK-2 | The logo file becomes public in an Apache-2.0 repository (the licence grants no trademark rights) | Certain, low: the logo is already on the website | Accept |
| RISK-3 | An instance run by someone else shows "by Meaningfy" | Certain, none: it stays true | Accept |
| RISK-4 | Meaningfy changes its logo | Low, low: one icon to replace | Accept |

## After the EPIC was drafted

> well it is in fact meaningfy.lu, yes point to the licence link in the github

- The company link is `https://meaningfy.lu` (the agent had assumed `meaningfy.ws`).
- The licence links to `LICENSE` in the GitHub repository.

## Not checked

- How the logo reads at text height in a real browser.
