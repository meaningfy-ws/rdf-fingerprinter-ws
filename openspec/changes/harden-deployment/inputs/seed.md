# Seed (developer, 2026-11-08)

After both EPICs were archived, the closing summary listed what remained before production. The
developer answered:

> use apache2, , yes add as much restrinction as nedeed, okay on secrets, what do you need from me there?

- "use apache2": the licence is Apache-2.0 (`LICENSE` was GPLv3, `pyproject.toml` Apache-2.0).
- "add as much restriction as needed": restrict the outgoing traffic of the worker and the API
  (issue #35, `SECURITY.md`), and whatever else the deployment needs.
- "okay on secrets": give each container only the secrets it uses (the stage-4 review's deferred item).

Also reported: `make down` from the repo root failed for want of `infra/.env`.
