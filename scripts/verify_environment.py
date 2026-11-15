"""Import every requested dependency without touching system caches."""

import importlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))


def main():
    versions = {}
    for name in (
        "asf_search", "numpy", "xarray", "h5py", "h5netcdf", "fsspec",
        "scipy", "rasterio", "matplotlib", "streamlit",
    ):
        module = importlib.import_module(name)
        versions[name] = module.__version__
        print(f"OK {name} {versions[name]}")
    report = {"python": sys.version, "executable": sys.executable, "packages": versions}
    (ROOT / "data" / "environment_check.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
