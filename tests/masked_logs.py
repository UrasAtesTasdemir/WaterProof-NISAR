"""Hash records written before the release-time path masking (data/masked_logs.json) stay unchanged.

A recorded digest is honoured for a masked log only if it equals that log's original_sha256; the file must then match
masked_sha256 exactly. Every other file is compared with its recorded digest as before.
"""
import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / 'data/masked_logs.json'


def expected_digest(name, recorded):
    entry = json.loads(REGISTRY.read_text())['files'].get(name) if REGISTRY.exists() else None
    if entry and entry['original_sha256'] == recorded:
        return entry['masked_sha256']
    return recorded
