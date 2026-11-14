# Clarity gate: improve-ui-footer PLAN

Scored by the lead, 2026-11-14, on `design.md` + `tasks.md` + `specs/job-console/spec.md`. Run 1 of
at most 2 (SMALL).

| Criterion | Score | Note |
|---|---|---|
| Actionability | 2/2 | Each task names its files, its tests first and its check |
| Specificity | 1.5/2 | URLs, class names, sizes and the animation are given; the heart's path and the exact docs page are left to the builder |
| Consistency | 2/2 | The EPIC's Impact line was amended to agree with F-2 |
| Structure | 1.5/2 | Anti-patterns, error matrix, test map present; depth kept to the appetite |
| Disambiguation | 1/1 | "Installed version" settled for the images (F-2), no fallback |
| Reference clarity | 1/1 | Every decision cites its DEC; scenarios map to files |

**Total: 9/10. Pass.**

Attack before the gate (the lead): the version call fails in the images (found; F-2, the
developer's decision); the build backend could drop non-Python files (RISK-5, checked in task
1.1); the error page might not carry the footer (it extends `base.html`; in the scenario outline);
the wordmark at text height (RISK-6, shown at the demo).

Accepted gaps: none.
