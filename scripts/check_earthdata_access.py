"""Check NISAR HTTPS access using a secret token, without downloading products.

Interactive entry is local-terminal-only. Optional storage is outside source
code, ignored by Git, and restricted to the owner (directory 0700/file 0600).
"""

import argparse
from datetime import datetime, timezone
import getpass
import json
import logging
import os
from pathlib import Path
import sys
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
SECRET = ROOT / ".secrets" / "earthdata_token"
REPORT = ROOT / "data" / "earthdata_access_check.json"
TOKEN_VARIABLES = ("EARTHDATA_TOKEN", "NASA_EARTHDATA_TOKEN", "EARTHDATA_BEARER_TOKEN")
PRODUCT_HOST = "nisar.asf.earthdatacloud.nasa.gov"
# Observed in the HTTPS Location returned by the official NISAR endpoint.
# Exact distribution only; do not allow arbitrary cloudfront.net hosts.
PRODUCT_CDN_HOST = "d1mv8zhcvry6x4.cloudfront.net"


class AccessCheckError(Exception):
    """Only fixed, non-sensitive diagnostic messages are permitted here."""


def open_product_range(url, token, entry):
    """Follow bounded data redirects, never forwarding Bearer to another host.

    The caller must close the returned response. Redirect response bodies are
    never read, and signed URL paths/queries are never included in diagnostics.
    """
    entry["redirects"] = []
    for _ in range(6):
        parsed = urlparse(url)
        host = parsed.hostname or ""
        allowed_s3 = (
            host == "sds-n-cumulus-prod-nisar-products.s3.us-west-2.amazonaws.com"
            or (host == "s3.us-west-2.amazonaws.com"
                and parsed.path.startswith("/sds-n-cumulus-prod-nisar-products/"))
        )
        if (parsed.scheme != "https" or parsed.port not in (None, 443)
                or parsed.username or parsed.password
                or not (host in (PRODUCT_HOST, PRODUCT_CDN_HOST) or allowed_s3)):
            raise AccessCheckError("Redirect target is not an approved HTTPS NISAR data endpoint; no credentials sent to it.")
        headers = {"Range": "bytes=0-7", "Accept-Encoding": "identity"}
        if host == PRODUCT_HOST:
            headers["Authorization"] = "Bearer " + token
        response = requests.get(url, headers=headers, stream=True,
                                allow_redirects=False, timeout=(15, 45))
        entry["http_status"] = response.status_code
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        target = urljoin(url, response.headers.get("Location", ""))
        target_host = urlparse(target).hostname
        entry["redirects"].append({"http_status": response.status_code,
                                   "from_host": host, "to_host": target_host})
        response.close()
        if target_host == "urs.earthdata.nasa.gov":
            raise AccessCheckError("Redirected to Earthdata Login instead of HDF5 data. Token acceptance or application/EULA authorization must be checked; this response alone cannot distinguish them.")
        if not response.headers.get("Location"):
            raise AccessCheckError("Data redirect did not include a Location header.")
        url = target
    raise AccessCheckError("NISAR data redirect limit reached.")


def available_token():
    for name in TOKEN_VARIABLES:
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    if SECRET.is_file():
        if SECRET.is_symlink() or SECRET.stat().st_mode & 0o077:
            raise ValueError("Local credential file must be owner-only and not a symlink.")
        return SECRET.read_text(encoding="utf-8").strip()
    return None


def write_report(report):
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="store_true", help="Enter a token using a hidden local terminal prompt.")
    parser.add_argument("--save-token", action="store_true", help="Save a verified token to ignored .secrets/earthdata_token with permissions 0600.")
    args = parser.parse_args()
    # HTTP debug logging can disclose Authorization headers. Do not enable it.
    logging.disable(logging.CRITICAL)
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "not_checked", "products": [],
              "full_products_downloaded": False}
    try:
        manifest = json.loads((ROOT / "data" / "nisar_manifest.json").read_text())
        observations = manifest["observations"]
        if len(observations) != 2:
            raise ValueError("Expected exactly two manifest observations.")
        for item in observations:
            url = urlparse(item["download_url"])
            if (url.scheme != "https" or url.hostname != "nisar.asf.earthdatacloud.nasa.gov"
                    or url.username or url.password or url.query or url.fragment
                    or not url.path.endswith("/" + item["product_id"] + ".h5")):
                raise ValueError("Manifest contains an unexpected product URL.")
        token = available_token()
        if args.prompt:
            if not sys.stdin.isatty():
                raise ValueError("Hidden entry requires a local interactive terminal.")
            token = getpass.getpass("Earthdata Bearer Token (hidden; never enter in chat): ").strip()
        if not token:
            report["status"] = "blocked_missing_credentials"
            report["detail"] = "No supported environment token or local protected token file is available. Product access was not attempted."
            write_report(report)
            print(report["detail"])
            return 2
        if any(char.isspace() for char in token):
            raise ValueError("Token must not contain whitespace.")
        for item in observations:
            entry = {"product_id": item["product_id"]}
            report["products"].append(entry)
            with open_product_range(item["download_url"], token, entry) as response:
                entry["http_status"] = response.status_code
                if response.status_code != 206:
                    report["status"] = "blocked_http_access"
                    report["detail"] = f"Product access returned HTTP {response.status_code}; expected 206 Partial Content. No response body was read."
                    write_report(report)
                    print(report["detail"])
                    return 2
                if not response.headers.get("Content-Range", "").startswith("bytes 0-7/"):
                    raise ValueError("Server did not honor the requested eight-byte range.")
                signature = response.raw.read(8)
                entry["hdf5_signature_verified"] = signature == b"\x89HDF\r\n\x1a\n"
                entry["bytes_read"] = len(signature)
                if not entry["hdf5_signature_verified"]:
                    raise ValueError("The product response did not start with the HDF5 signature.")
        if args.save_token:
            SECRET.parent.mkdir(mode=0o700, exist_ok=True)
            if SECRET.parent.is_symlink():
                raise ValueError("Credential directory must not be a symlink.")
            SECRET.parent.chmod(0o700)
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
            fd = os.open(SECRET, flags, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(token + "\n")
        report["status"] = "product_access_verified"
        report["detail"] = "Both HDF5 signatures verified using eight-byte HTTPS ranges. HHHH layers and radar arrays have not been read."
        write_report(report)
        print(report["detail"])
        return 0
    except AccessCheckError as exc:
        report["status"] = "blocked_redirect_access"
        report["detail"] = str(exc)
        write_report(report)
        print(report["detail"])
        return 2
    except Exception as exc:
        # Do not print exception messages, request headers, response bodies or
        # traceback locals: any of these could contain a token.
        report["status"] = "blocked_check_error"
        report["error_type"] = type(exc).__name__
        write_report(report)
        print(f"Access check stopped ({type(exc).__name__}); secret-bearing exception details suppressed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
