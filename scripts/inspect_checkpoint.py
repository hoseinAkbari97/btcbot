"""Print the protocol-relevant fields of a segmented-research checkpoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    print(f"checkpoint: {path}")
    for key in (
        "dataset_path",
        "dataset_sha256",
        "bar_index",
        "last_open_time",
        "engine_version",
        "state_schema_version",
        "config_hash",
        "events_written",
        "events_bytes",
        "segments_done",
        "complete",
    ):
        print(f"{key}: {data.get(key)}")
    setup1 = data.get("setup1") or {}
    if not setup1:
        print("setup1: <absent>")
        return
    print("setup1.config:", json.dumps(setup1.get("config"), indent=2))
    print("setup1.counts:", json.dumps(setup1.get("counts"), indent=2))
    print("setup1.episodes:", setup1.get("episodes"))
    print("setup1.gaps:", len((setup1.get("gap_index") or {}).get("gaps", [])))


if __name__ == "__main__":
    main()
