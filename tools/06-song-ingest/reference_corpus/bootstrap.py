#!/usr/bin/env python3
"""One-shot reference-corpus bootstrap (spec §12 Phase D+E):

1. init the corpus layout in content-tools
2. ingest the canonical composition from music_creation (hashes + maps)
3. build + validate the Suno Rendering Prompt Book (86/90 targets × 2)

    PYTHONPATH=tools/06-song-ingest python -m reference_corpus.bootstrap
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools" / "06-song-ingest"))

from reference_corpus import corpus, ontology  # noqa: E402
from reference_corpus import build_book  # noqa: E402


def main() -> int:
    targets = ontology.load_targets()
    print(f"ontology: {len(targets)} documented Suno Advanced Split targets "
          f"from {ontology.TARGETS_DIR}")

    source = Path(ontology.DEFAULT_REPO) / "reference_composition" / "output"
    if not source.is_dir():
        print(f"canonical composition output missing: {source}\n"
              f"run: (music_creation) python -m "
              f"reference_composition.generator.build", file=sys.stderr)
        return 2

    index = corpus.init_corpus(REPO_ROOT, composition_source=source,
                               targets=targets)
    print(f"corpus: {len(index['targets'])} target dirs initialized at "
          f"{corpus.CANONICAL_DIR}")

    built = build_book.build_all(REPO_ROOT)
    if not built:
        return 2
    book = build_book.write_book(REPO_ROOT, built)
    r = built["report"]
    print(f"prompt book: {book}")
    print(f"{r['prompt_count']} prompts across {r['targets']} targets — "
          f"all_ok={r['all_ok']}")
    if not r["all_ok"]:
        return 1

    # linkage: record ontology + composition provenance inside the piece dir
    linkage = {
        "ontology": {"source_repo": ontology.DEFAULT_REPO,
                     "targets": len(targets),
                     "standard": 22, "beta_total": len(targets) - 22},
        "composition": index["composition_artifacts"],
        "prompt_validation": {"rules": r["rules"], "all_ok": r["all_ok"]},
    }
    piece = REPO_ROOT / corpus.CANONICAL_DIR
    (piece / "ontology-linkage.json").write_text(
        json.dumps(linkage, indent=2) + "\n")
    print("ontology-linkage.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
