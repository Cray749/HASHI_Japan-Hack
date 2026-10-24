"""Download the optional translation model (NLLB-200 distilled 600M, int8) into models/.

Needs internet once. Licence: CC-BY-NC 4.0 (non-commercial), so this is an optional extra for the
live translator page, never part of the request matching path.
"""
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "models" / "nllb-600m-ct2"
snapshot_download("JustFrederik/nllb-200-distilled-600M-ct2-int8", local_dir=str(target))
hf_hub_download("facebook/nllb-200-distilled-600M", "sentencepiece.bpe.model", local_dir=str(target))
print("ready:", target, [p.name for p in target.iterdir()])
