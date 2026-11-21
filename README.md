# Wexum

Wexum is a planned global technology ecosystem by **IhsanSoft**, with standalone applications and one integrated **Wexum Hub**. The repository is the **source of truth** for specifications, decisions, task ownership and code. No product is claimed to be ready for public release.

**Start here:** [AGENTS.md](AGENTS.md) → [current state](docs/engineering/STATE.md) → [architecture](docs/architecture/SYSTEM.md) → [product catalog](docs/catalog/products.json).

## Principles
- Standalone products remain useful independently of Hub.
- Explicit service boundaries, least-privilege permissions and user-controlled data sharing.
- Production behavior must be demonstrated through tests and evidence, not claimed as "perfect".
- Conservative engineering: straightforward code, minimal dependencies, independently reviewable changes.
- No prohibited or unresolved features are shipped before documented ethical review.
- FileShape is a separate IhsanSoft product; any integration must use an agreed API and does not imply a shared account.

## First code
The initial executable code is a tiny, dependency-free authorization and event-contract library under `src/wexum_core`. It is **not** an identity server, VPN engine, payment service or production-ready security system.

Run locally with Python 3.12+:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

See [engineering workflow](docs/engineering/MULTI_AGENT.md) and [quality gates](docs/engineering/QUALITY.md). Work in a task-specific branch and submit a PR; do not push directly to main.

**Naming:** do not assign product release numbers before a real public release. Use "plan", "specification", "architecture" and "stage" in pre-release documents.

