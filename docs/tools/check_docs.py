"""Docs consistency check (run by `make check-docs`): every page is reachable from the navigation."""
import re
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "modules/ROOT"


def main() -> int:
    linked = set(re.findall(r"xref:([\w./\-]+\.adoc)", (MODULE / "nav.adoc").read_text()))
    pages = sorted(p.relative_to(MODULE / "pages").as_posix() for p in (MODULE / "pages").rglob("*.adoc"))
    errors = [f"page not in nav: {p}" for p in pages if p not in linked]
    for e in errors:
        print(f"FAIL {e}")
    print(f"{len(errors)} problem(s)" if errors else "docs check passed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
