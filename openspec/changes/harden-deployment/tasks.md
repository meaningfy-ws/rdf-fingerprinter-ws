> Derives from: EPIC `harden-deployment` (`proposal.md`, DEC-1 to DEC-7); design H-1 to H-6.

## 1. Hardening

- [x] 1.1 DEC-7: `LICENSE` Apache-2.0, README.
- [ ] 1.2 H-5: secret keys required per app (`config.py`, `bootstrap.py`); tests "Each app needs only its key".
- [ ] 1.3 H-1 to H-4: networks, `infra/proxy/squid.conf`, `infra/edge/nginx.conf`, `infra/compose.dev.yaml`, per-service environment in `infra/compose.yaml`; tests in `tests/unit/test_infra_env.py` ("Networks are pinned", "The worker holds no Flask key", the proxy variables and ranges).
- [ ] 1.4 H-6: `make init-env`, `make down` without `.env`, `up-deps`/`up-dev` with the override; README, `SECURITY.md`, CHANGELOG, `AGENTS.md`.
- [ ] 1.5 Acceptance on a clean clone (`evidence/acceptance.md`): the success measure; PR into `develop`; archive.

## Roadmap

- [x] 1.1 · [ ] 1.2 · [ ] 1.3 · [ ] 1.4 · [ ] 1.5

## Verification

`openspec validate harden-deployment --strict`; `make check-all`, `make test-containers`,
`make build-images` green; the acceptance run.
