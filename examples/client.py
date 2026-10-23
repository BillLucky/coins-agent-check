#!/usr/bin/env python3
"""Small x402 HTTP examples. No wallet keys, signing or automatic payments.

Python 3.11+, standard library only. See README.md before preparing a purchase.
"""
import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://coins.zhidun.ai"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAID = {"bsc-reconcile": "/v1/bsc/reconcile", "usdc-receipt": "/api/v1/payments/usdc-receipt",
        "erc20-allowances": "/api/v1/tokens/allowances"}
HERE = Path(__file__).resolve().parent


class ExampleError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise ExampleError("Redirect refused; keep the original purchase origin.")


def origin(value):
    p = urllib.parse.urlsplit(value)
    local = p.hostname in {"127.0.0.1", "localhost", "::1"}
    if (p.scheme != "https" and not (local and p.scheme == "http")) or not p.hostname or p.username or p.password or p.path not in {"", "/"} or p.query or p.fragment:
        raise ExampleError("Use an HTTPS origin, or loopback HTTP for local tests.")
    return value.rstrip("/")


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def private_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_mode & 0o077:
        raise ExampleError("Choose a private output directory with mode 0700.")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(encode(value) + "\n")


def private_text(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 64_000:
        raise ExampleError("Private input must be a regular, non-symlink file, mode 0600 and <=64 KB.")
    return path.read_text()


def request(base, path, body=None, headers=None):
    data = body.encode() if isinstance(body, str) else None
    req = urllib.request.Request(origin(base) + path, data=data,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        response = urllib.request.build_opener(NoRedirect).open(req, timeout=25)
    except urllib.error.HTTPError as error:
        response = error
    except (OSError, urllib.error.URLError):
        raise ExampleError("Network result unknown. Preserve the original request/key/authorization; do not create another payment.") from None
    with response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ExampleError("Response too large; preserve the original purchase state.")
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise ExampleError("Non-JSON response; preserve the original purchase state.") from None
        return response.status, {key.lower(): value for key, value in response.headers.items()}, value


def requirements(challenge, base, path):
    if challenge.get("x402Version") != 2 or challenge.get("resource", {}).get("url") != origin(base) + path:
        raise ExampleError("Payment version or resource does not match the requested service.")
    accepts = challenge.get("accepts", [])
    if len(accepts) != 1:
        raise ExampleError("Expected exactly one payment option.")
    accepted = accepts[0]
    if (accepted.get("scheme") != "exact" or accepted.get("network") != "eip155:8453"
            or accepted.get("amount") != "20000" or accepted.get("asset", "").lower() != USDC.lower()
            or accepted.get("extra", {}).get("assetTransferMethod") != "eip3009"
            or not re.fullmatch(r"0x[0-9a-fA-F]{40}", accepted.get("payTo", ""))
            or int(accepted["payTo"], 16) == 0):
        raise ExampleError("Unexpected amount, receiver, asset, network or transfer method; do not sign.")
    return accepted


def inspect(base, service):
    path = PAID[service]
    status, _headers, body = request(base, path, "{}")
    if status != 402:
        raise ExampleError(f"Expected payment terms, got HTTP {status}: {body.get('error', 'unavailable')}. No payment attempted.")
    requirements(body, base, path)
    return body


def prepare(base, service, input_path, country, accepted_terms, state_path):
    if not accepted_terms or not re.fullmatch(r"[A-Z]{2}", country or "") or country in {"CN", "ZZ", "AA"}:
        raise ExampleError("Declare the actual eligible customer's country and explicitly accept the live terms.")
    body = json.loads(Path(input_path).read_text())
    if not isinstance(body, dict) or re.search(r"REPLACE|<[^>]+>", encode(body)):
        raise ExampleError("Replace all illustrative placeholders with authorized public-chain input.")
    if any(re.search(r"private.?key|seed|mnemonic|secret|password", key, re.I) for key in body):
        raise ExampleError("Request bodies must not contain wallet credentials.")
    if service != "bsc-reconcile":
        body.update(customerCountryCode=country, termsAccepted=True)
    challenge = inspect(base, service)
    state = {"origin": origin(base), "service": service, "path": PAID[service], "body": encode(body),
             "customerCountryCode": country, "idempotencyKey": secrets.token_urlsafe(32),
             "challenge": challenge, "createdAt": dt.datetime.now(dt.timezone.utc).isoformat()}
    private_json(state_path, state)
    return {"prepared": str(state_path), "paymentAttempted": False,
            "next": "Use an approved compatible x402 buyer to authorize the saved exact request and payment terms. Keep its PAYMENT-SIGNATURE private."}


def submit(state_path, payment_path, expected_pay_to, send=False):
    state = json.loads(private_text(state_path))
    if PAID.get(state["service"]) != state["path"]:
        raise ExampleError("Unknown service or modified path.")
    accepted = requirements(state["challenge"], state["origin"], state["path"])
    if accepted["payTo"].lower() != expected_pay_to.lower():
        raise ExampleError("Receiver does not match the independently approved address.")
    signature = private_text(payment_path).strip()
    try:
        payment = json.loads(base64.b64decode(signature, validate=True))
    except (ValueError, UnicodeDecodeError):
        raise ExampleError("Expected the buyer's base64 PAYMENT-SIGNATURE header, not a private key.") from None
    if not isinstance(payment, dict) or not isinstance(payment.get("payload"), dict):
        raise ExampleError("Expected an x402 v2 payment object from an approved compatible buyer.")
    authorization = payment["payload"].get("authorization", {})
    if not isinstance(authorization, dict):
        raise ExampleError("Missing structured buyer authorization.")
    if (payment.get("x402Version") != 2 or payment.get("accepted") != accepted
            or payment.get("resource", {}).get("url") != state["origin"] + state["path"]
            or authorization.get("to", "").lower() != accepted["payTo"].lower()
            or authorization.get("value") != "20000"):
        raise ExampleError("Buyer authorization does not match the prepared purchase.")
    if not send:
        return {"dryRun": True, "paymentAttempted": False,
                "next": "Review the saved request and your buyer authorization. --send submits it and may settle 0.02 Base USDC."}
    # Freeze both the exact body/key and original authorization BEFORE sending.
    # A timeout must never lead this example to silently accept a fresh payment.
    frozen = {"state": state, "paymentSignature": signature}
    attempt = Path(state_path).with_suffix(".attempt.json")
    if attempt.exists():
        if json.loads(private_text(attempt)) != frozen:
            raise ExampleError("Purchase changed after its first attempt. Recover the original state and authorization; do not sign a replacement.")
    else:
        private_json(attempt, frozen)
    headers = {"Idempotency-Key": state["idempotencyKey"], "PAYMENT-SIGNATURE": signature}
    if state["service"] == "bsc-reconcile":
        headers.update({"X-Customer-Country": state["customerCountryCode"], "X-Terms-Accepted": "true"})
    status, response_headers, value = request(state["origin"], state["path"], state["body"], headers)
    path = Path(state_path).parent / ("response-" + secrets.token_hex(8) + ".json")
    private_json(path, {"status": status, "paymentResponse": response_headers.get("payment-response"), "body": value})
    return {"httpStatus": status, "savedPrivately": str(path),
            "guidance": "A 200 is a delivered report. For interrupted/unknown results, retry with this same state and original authorization. Never generate another payment to resolve uncertainty."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=ORIGIN)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog")
    commands.add_parser("demo")
    commands.add_parser("cost")
    calldata = commands.add_parser("calldata")
    calldata.add_argument("--input", type=Path, default=HERE / "calldata.example.json")
    challenge = commands.add_parser("challenge")
    challenge.add_argument("--service", choices=PAID, required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--service", choices=PAID, required=True)
    prep.add_argument("--input", type=Path, required=True)
    prep.add_argument("--country", required=True)
    prep.add_argument("--accept-terms", action="store_true")
    prep.add_argument("--state", type=Path, required=True)
    paid = commands.add_parser("submit")
    paid.add_argument("--state", type=Path, required=True)
    paid.add_argument("--payment-file", type=Path, required=True)
    paid.add_argument("--expected-pay-to", required=True)
    paid.add_argument("--send", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "catalog":
            status, _headers, result = request(args.base_url, "/api/v1/services")
            if status != 200:
                raise ExampleError(f"Catalog unavailable: HTTP {status}")
        elif args.command == "demo":
            status, _headers, result = request(args.base_url, "/demo/usdc-receipt.json")
            if status != 200 or result.get("sampleOnly") is not True or result.get("paymentAttempted") is not False:
                raise ExampleError(f"Fixed public example unavailable: HTTP {status}. No payment attempted.")
        elif args.command == "cost":
            body = json.loads((HERE / "cost.example.json").read_text())
            body["quoteAt"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
            status, _headers, result = request(args.base_url, "/api/v1/costs/preflight", encode(body))
            if status != 200:
                raise ExampleError(f"Free calculation rejected: HTTP {status}")
        elif args.command == "calldata":
            status, _headers, result = request(args.base_url, "/api/v1/evm/calldata", Path(args.input).read_text())
            if status != 200:
                raise ExampleError(f"Free interpretation rejected: HTTP {status}")
        elif args.command == "challenge":
            result = inspect(args.base_url, args.service)
        elif args.command == "prepare":
            result = prepare(args.base_url, args.service, args.input, args.country, args.accept_terms, args.state)
        else:
            result = submit(args.state, args.payment_file, args.expected_pay_to, args.send)
        print(json.dumps(result, indent=2))
    except (ExampleError, ValueError, OSError, KeyError) as error:
        # Do not echo file contents, private keys, signed payloads or request keys.
        message = str(error) if isinstance(error, ExampleError) else "Invalid input or unavailable local file; preserve the original purchase state."
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
