"""Discover public NISAR metadata only; never open or download HDF5 files."""

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

import asf_search as asf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REFERENCE = "https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/"
AOI = "POLYGON((-90.31002 29.902604, -90.250797 29.902604, -90.250797 29.924476, -90.31002 29.924476, -90.31002 29.902604))"
DATES = ("2026-06-21", "2026-07-03")
# Official GCOV filename convention; no example observation IDs are hard-coded.
NAME = re.compile(
    r"^NISAR_(?P<instrument>[LS])2_PR_GCOV_(?P<cycle>\d{3})_"
    r"(?P<track>\d{3})_(?P<direction>[AD])_(?P<frame>\d{3})_"
    r"(?P<bandwidth>\d{4})_(?P<polarization>[A-Z]{4})_(?P<source>[AM])_"
    r"(?P<start>\d{8}T\d{6})_(?P<end>\d{8}T\d{6})_"
    r"(?P<crid>[PX]\d{5})_(?P<accuracy>[PMNF])_(?P<coverage>[FP])_"
    r"(?P<location>[A-Z])_(?P<counter>\d{3})\.h5$"
)
COMPATIBILITY = (
    "instrument", "track", "direction", "frame", "bandwidth",
    "polarization", "source", "crid",
)


def save(name, value):
    (DATA / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def parse_product(url, target):
    filename = unquote(Path(urlparse(url).path).name)
    match = NAME.fullmatch(filename)
    if not match:
        return None
    fields = match.groupdict()
    start = datetime.strptime(fields["start"], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    if start.date().isoformat() != target:
        return None
    # SH, DH and QP contain HH in frequency A, per ASF's naming guide.
    if fields["polarization"][:2] not in {"SH", "DH", "QP"}:
        return None
    return {
        "product_id": filename.removesuffix(".h5"),
        "start_time_utc": start.isoformat(),
        "end_time_utc": datetime.strptime(fields["end"], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).isoformat(),
        "product_type": "L2_GCOV", "data_maturity": "PROVISIONAL",
        "requested_polarization": "HH", "gcov_layer": "frequencyA/HHHH",
        "download_url": url, "filename_fields": fields,
    }


def main():
    DATA.mkdir(exist_ok=True)
    report = {
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "reference": REFERENCE, "aoi_wkt": AOI, "target_dates_utc": DATES,
        "queries": [], "products": [], "compatible_pairs": [],
        "hdf5_downloaded": False, "url_access_verified": False,
    }
    try:
        for target in DATES:
            end = date.fromisoformat(target) + timedelta(days=1)
            query = {
                "dataset": ["NISAR"], "processingLevel": ["GCOV"],
                "productionConfiguration": ["PR"], "dataMaturity": "PROVISIONAL",
                "flightDirection": "ASCENDING",
                "intersectsWith": AOI, "start": target + "T00:00:00Z",
                "end": end.isoformat() + "T00:00:00Z", "maxResults": 250,
            }
            print(f"Searching ASF: {target} (UTC)", flush=True)
            results = asf.search(opts=asf.ASFSearchOptions(**query))
            save(f"nisar_search_{target}.geojson", results.geojson())
            report["queries"].append({"options": query, "result_count": len(results)})
            if len(results) >= query["maxResults"]:
                raise RuntimeError("Search limit reached; refine the query before selecting a pair.")
            latest = {}
            # Query exactly as the Cookbook: filter HH locally. The API-side
            # mainBandPolarization='HH' filter returned zero for these HH+HV
            # acquisitions even though the returned metadata lists HH.
            url_records = {
                url: record for record in results
                for url in record.find_urls(extension=".h5", pattern=r"^(?!.*QA_STATS).*", directAccess=False)
            }
            for url, record in sorted(url_records.items()):
                props = record.properties
                if "HH" not in (props.get("mainBandPolarization") or []):
                    continue
                if props.get("collectionName") != "NISAR_L2_GCOV_PROVISIONAL_V1":
                    continue
                product = parse_product(url, target)
                if product is None:
                    continue
                fields = product["filename_fields"]
                if props.get("pathNumber") != int(fields["track"]) or props.get("frameNumber") != int(fields["frame"]):
                    raise ValueError("Catalog track/frame disagree with the product filename")
                product["catalog_metadata"] = {
                    key: props.get(key) for key in (
                        "fileID", "startTime", "stopTime", "processingLevel",
                        "collectionName", "pathNumber", "frameNumber",
                        "flightDirection", "mainBandPolarization", "sideBandPolarization",
                        "rangeBandwidth", "productionConfiguration", "crid", "pgeVersion",
                    )
                }
                product["s3_urls"] = record.find_urls(extension=".h5", pattern=r"^(?!.*QA_STATS).*", directAccess=True)
                # Cookbook: retain highest CRID for each acquisition identity.
                identity = product["product_id"].split("_" + product["filename_fields"]["crid"])[0]
                previous = latest.get(identity)
                if previous is None or product["filename_fields"]["crid"] > previous["filename_fields"]["crid"]:
                    latest[identity] = product
            report["products"].extend(latest.values())
            print(f"  {len(results)} catalog records; {len(latest)} eligible HDF5 products", flush=True)

        first = [p for p in report["products"] if p["start_time_utc"].startswith(DATES[0])]
        second = [p for p in report["products"] if p["start_time_utc"].startswith(DATES[1])]
        for left in first:
            for right in second:
                if all(left["filename_fields"][k] == right["filename_fields"][k] for k in COMPATIBILITY):
                    report["compatible_pairs"].append([left["product_id"], right["product_id"]])
        report["both_observations_found"] = bool(report["compatible_pairs"])
        if report["both_observations_found"]:
            selected_ids = report["compatible_pairs"][0]
            selected = [next(p for p in report["products"] if p["product_id"] == pid) for pid in selected_ids]
            save("nisar_manifest.json", {
                "queried_at_utc": report["queried_at_utc"], "reference": REFERENCE,
                "aoi_wkt": AOI, "observations": selected,
                "compatibility_fields": COMPATIBILITY,
                "verification_scope": "Public catalog metadata and filename configuration only; HDF5 contents and authenticated download access not verified.",
            })
        save("nisar_search_report.json", report)
        print(json.dumps(report, indent=2))
        return 0 if report["both_observations_found"] else 2
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        save("nisar_search_report.json", report)
        print(report["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
