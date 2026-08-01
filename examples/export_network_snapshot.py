"""Export the committed seed network as the static snapshot for the web app.

Writes frontend/public/network.json — the exact /api/network payload — so the
GitHub Pages build renders the real lineage (seeds, forks, accepted ideas,
vanished branches) with no backend. Regenerate whenever network/ changes:

    python examples/export_network_snapshot.py
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from observatory import ObservatoryServer, ObservatoryHandler  # noqa: E402


def main():
    server = ObservatoryServer(("127.0.0.1", 0), ObservatoryHandler, ROOT)
    # The public snapshot contains only committed seeds — never local nodes
    # (they carry identities and live under gitignored nodes/).
    server.nodes_dir = Path(tempfile.mkdtemp())
    server.reindex()
    payload = server.network_payload()
    server.server_close()

    out = ROOT / "frontend" / "public" / "network.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    s = payload["stats"]
    print(
        f"wrote {out.relative_to(ROOT)} "
        f"({s['branches']} branches, {s['live']} live, "
        f"{s['vanished']} vanished, {s['ideas']} ideas)"
    )


if __name__ == "__main__":
    main()
