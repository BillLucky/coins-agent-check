import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "public/examples/client.py" if (ROOT / "public/examples/client.py").exists() else ROOT / "examples/client.py"
SPEC = importlib.util.spec_from_file_location("example_client", FILE)
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)
RECEIVER = "0x" + "1" * 40


def challenge():
    return {"x402Version": 2, "resource": {"url": client.ORIGIN + client.PAID["usdc-receipt"]},
            "accepts": [{"scheme": "exact", "network": "eip155:8453", "amount": "20000",
                         "asset": client.USDC, "payTo": RECEIVER,
                         "extra": {"assetTransferMethod": "eip3009"}}]}


class ExampleClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.state_path = self.root / "state.json"
        self.payment_path = self.root / "payment.txt"
        self.state = {"origin": client.ORIGIN, "service": "usdc-receipt", "path": client.PAID["usdc-receipt"],
                      "body": '{"chainId":8453}', "customerCountryCode": "US",
                      "idempotencyKey": "example_test_retrieval_key_0001", "challenge": challenge()}
        client.private_json(self.state_path, self.state)
        self.payment = {"x402Version": 2, "accepted": challenge()["accepts"][0],
                        "resource": challenge()["resource"], "payload": {"signature": "synthetic-non-wallet-fixture",
                        "authorization": {"to": RECEIVER, "value": "20000", "nonce": "fixture-original-nonce"}}}
        self.write_payment()

    def write_payment(self):
        self.payment_path.write_text(base64.b64encode(json.dumps(self.payment).encode()).decode())
        self.payment_path.chmod(0o600)

    def test_origin_disallows_credentials_paths_and_remote_plaintext(self):
        for value in ["http://example.com", "https://user:pass@example.com", "https://example.com/path",
                      "https://example.com?token=example"]:
            with self.subTest(value=value), self.assertRaises(client.ExampleError):
                client.origin(value)
        self.assertEqual(client.origin("http://127.0.0.1:7042"), "http://127.0.0.1:7042")

    def test_discovery_checks_price_asset_network_resource_and_receiver(self):
        for key, value in [("amount", "20001"), ("network", "eip155:56"), ("asset", RECEIVER),
                           ("payTo", "0x" + "0" * 40)]:
            invalid = challenge()
            invalid["accepts"][0][key] = value
            with self.subTest(key=key), self.assertRaises(client.ExampleError):
                client.requirements(invalid, client.ORIGIN, client.PAID["usdc-receipt"])
        invalid = challenge()
        invalid["resource"]["url"] = "https://unapproved.invalid/api"
        with self.assertRaises(client.ExampleError):
            client.requirements(invalid, client.ORIGIN, client.PAID["usdc-receipt"])

    def test_dry_run_does_not_send_or_freeze_payment(self):
        with patch.object(client, "request") as request:
            result = client.submit(self.state_path, self.payment_path, RECEIVER)
        request.assert_not_called()
        self.assertTrue(result["dryRun"])
        self.assertFalse(self.state_path.with_suffix(".attempt.json").exists())
        self.assertNotIn(self.state["idempotencyKey"], json.dumps(result))

    def test_identical_retry_keeps_the_same_body_key_and_original_authorization(self):
        with patch.object(client, "request", return_value=(200, {"payment-response": "fixture-receipt"}, {"kind": "fixture_report"})) as request:
            first = client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
            client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
        self.assertEqual(request.call_args_list[0], request.call_args_list[1])
        headers = request.call_args_list[0].args[3]
        self.assertEqual(headers["Idempotency-Key"], self.state["idempotencyKey"])
        response = json.loads(client.private_text(first["savedPrivately"]))
        self.assertEqual(response["paymentResponse"], "fixture-receipt")
        self.assertEqual(Path(first["savedPrivately"]).stat().st_mode & 0o777, 0o600)

    def test_replacement_payment_and_modified_body_are_refused_after_first_send(self):
        with patch.object(client, "request", return_value=(503, {}, {"error": "unknown"})) as request:
            client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
            self.payment["payload"]["authorization"]["nonce"] = "fixture-replacement-nonce"
            self.write_payment()
            with self.assertRaises(client.ExampleError):
                client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
            self.payment["payload"]["authorization"]["nonce"] = "fixture-original-nonce"
            self.write_payment()
            self.state["body"] = '{"chainId":56}'
            self.state_path.write_text(json.dumps(self.state))
            with self.assertRaises(client.ExampleError):
                client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
            self.assertEqual(request.call_count, 1)

    def test_unknown_network_result_freezes_purchase_before_any_retry(self):
        with patch.object(client, "request", side_effect=client.ExampleError("unknown network result")):
            with self.assertRaises(client.ExampleError):
                client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
        frozen = json.loads(client.private_text(self.state_path.with_suffix(".attempt.json")))
        self.assertEqual(frozen["state"], self.state)
        self.assertEqual(frozen["paymentSignature"], self.payment_path.read_text())

    def test_wrong_approved_receiver_or_buyer_terms_never_sends(self):
        with patch.object(client, "request") as request:
            with self.assertRaises(client.ExampleError):
                client.submit(self.state_path, self.payment_path, "0x" + "2" * 40, send=True)
            self.payment["payload"]["authorization"]["value"] = "40000"
            self.write_payment()
            with self.assertRaises(client.ExampleError):
                client.submit(self.state_path, self.payment_path, RECEIVER, send=True)
            request.assert_not_called()

    def test_public_permission_or_symlink_inputs_are_refused(self):
        self.payment_path.chmod(0o644)
        with self.assertRaises(client.ExampleError):
            client.submit(self.state_path, self.payment_path, RECEIVER)
        self.payment_path.chmod(0o600)
        linked = self.root / "linked.txt"
        linked.symlink_to(self.payment_path)
        with self.assertRaises(client.ExampleError):
            client.private_text(linked)
        public = self.root / "shared"
        public.mkdir(mode=0o755)
        with self.assertRaises(client.ExampleError):
            client.private_json(public / "private.json", {})

    def test_preparation_refuses_placeholders_and_requires_real_country_acceptance(self):
        input_path = self.root / "input.json"
        input_path.write_text('{"txHash":"REPLACE_WITH_AUTHORIZED_HASH"}')
        for country, terms in [("CN", True), ("US", False), (None, True)]:
            with self.subTest(country=country), self.assertRaises(client.ExampleError):
                client.prepare(client.ORIGIN, "usdc-receipt", input_path, country, terms, self.root / "new.json")
        with self.assertRaises(client.ExampleError):
            client.prepare(client.ORIGIN, "usdc-receipt", input_path, "US", True, self.root / "new.json")
        input_path.write_text('{"chainId":8453,"txHash":"fixture"}')
        with patch.object(client, "inspect", return_value=challenge()):
            result = client.prepare(client.ORIGIN, "usdc-receipt", input_path, "US", True, self.root / "new.json")
        new = json.loads(client.private_text(self.root / "new.json"))
        self.assertFalse(result["paymentAttempted"])
        self.assertEqual(json.loads(new["body"])["customerCountryCode"], "US")
        self.assertTrue(json.loads(new["body"])["termsAccepted"])
        self.assertNotEqual(new["idempotencyKey"], self.state["idempotencyKey"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
