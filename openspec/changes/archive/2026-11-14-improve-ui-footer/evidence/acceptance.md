# Acceptance: improve-ui-footer (2026-11-14)

Run by the lead: the UI over the tests' fake API (three sample jobs) on `127.0.0.1:8765`, shown to
the developer live and as screenshots (light and dark, 1100 px and 360 px).

| Shown | Verdict |
|---|---|
| First shape: one row, "Made with ♥ by [logo]" | Rejected by the developer: "it looks a bit weird". Four variants mocked; the developer chose the third ("go with option 3") |
| Re-shape (DEC-8, R-5): the logo on its own, "Made with ♥ in Luxembourg" under it, the links, licence and version on the right; three centred lines at 360 px; the heart's own red on both themes | Shown; the developer asked to merge, close and archive ("okay pr merge to develop, close the change, archive it") |

Against the success measure: the feature scenarios pass for the jobs list, the new-job page, the
report viewer and the error page; the three links and the version are asserted; the stylesheet's
reduced-motion rule is pinned. Gates on the final code: `make check-all` 663 passed;
`make build-images` passed with the image check; `make test-containers` 73 passed; CI green.

Not shown: a screen reader's reading of the footer (asserted through the markup only).
