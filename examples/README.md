# Five service examples

Python 3.11+ and curl. The Python client uses only the standard library. Download these files together or clone [the public integration repository](https://github.com/BillLucky/coins-agent-check). The live origin is `https://coins.zhidun.ai`.

The first commands are free. Paid preparation only inspects terms and creates local files; it does not sign or pay. `submit` is a dry run unless you add `--send`. No private key, seed phrase, exchange key or wallet session is needed by this example client.

## 1. Discover all five tools

```sh
python3 examples/client.py catalog
curl --fail-with-body --silent --show-error https://coins.zhidun.ai/api/v1/services
```

`ready` is dependency status, not a guarantee of the next request or proof of customer eligibility. Read the live [terms](https://coins.zhidun.ai/privacy.html) and [schema](https://coins.zhidun.ai/openapi.json).

## 2. Free cost preflight

```sh
python3 examples/client.py cost
```

The client reads `cost.example.json` and refreshes `quoteAt` to the actual current UTC time. With the supplied assumptions, the expected `modeledProfitUsd` is `-0.0006996` and the result flags a modeled loss. Change the JSON assumptions before using it for your own analysis. This example does not query a market or execute a trade.

For curl, replace the timestamp with your actual quote time:

```sh
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/cost.example.json \
  https://coins.zhidun.ai/api/v1/costs/preflight
```

## 3. Free ERC-20 call interpretation

```sh
python3 examples/client.py calldata
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/calldata.example.json \
  https://coins.zhidun.ai/api/v1/evm/calldata
```

Expected fields include `interpretedAs: "approve"` and `flags: ["approves_max_uint256"]`. The addresses and ABI words are illustrative. This only interprets standard words; it does not sign, simulate, approve or identify a safe contract.

## 4. Inspect the three paid services without paying

```sh
python3 examples/client.py challenge --service bsc-reconcile
python3 examples/client.py challenge --service usdc-receipt
python3 examples/client.py challenge --service erc20-allowances
```

Expected response: x402 v2, exact scheme, `eip155:8453`, `amount: "20000"` (0.02 USDC), official Base USDC `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, the canonical requested resource and the current merchant `payTo`. The client checks the fixed terms. An HTTP 402 is a payment challenge, **not a charge or a delivered report**.

Paid API paths and templates:

| Service | POST path | Input template | What to inspect in a report |
|---|---|---|---|
| BSC transaction receipt | `/v1/bsc/reconcile` | `bsc-reconcile.template.json` | Transaction status, at least 12 confirmations, gas, token-event flows, `expectedTransferChecks` |
| Base USDC receipt | `/api/v1/payments/usdc-receipt` | `usdc-receipt.template.json` | `matchedReceivedRaw`, `minimumReceivedMet`, token payer separately from gas relayer; at least 20 L2 confirmations |
| Allowance snapshot | `/api/v1/tokens/allowances` | `erc20-allowances.template.json` | Canonical snapshot block, balance, spender allowances and `equalsMaxUint256`; no approval/revocation |

Base L2 depth is not Ethereum L1 finality. BSC inputs do not change the payment network. Evidence from one RPC is not an audit or guarantee of fulfillment or investment outcomes.

## 5. Prepare one actual request

Paid reports are only for actual eligible customers outside mainland China, where lawful. Do not use an Agent's server location as the customer's country. A restricted network returns JSON `403 region_not_supported` without attempting settlement. Do not route around this restriction.

1. Create a private local directory, then copy **one** template into it.
2. Replace every `REPLACE_...` value with authorized public-chain input. Remove `expectedPayer` if not needed. Set the actual customer country explicitly in the command below; no country is assumed by default.
3. Review the live terms before passing `--accept-terms`.

```sh
mkdir -p .local/example-purchase
chmod 700 .local/example-purchase
cp examples/usdc-receipt.template.json .local/example-purchase/input.json
chmod 600 .local/example-purchase/input.json
# Edit input.json first. Replace ACTUAL_COUNTRY with the real eligible country.
python3 examples/client.py prepare --service usdc-receipt \
  --input .local/example-purchase/input.json --country ACTUAL_COUNTRY \
  --accept-terms --state .local/example-purchase/state.json
```

For BSC or allowances, use the corresponding template and `--service`. The client supplies new-route country/terms declarations in JSON; legacy BSC declarations are sent as headers at submission. Preparation refuses unchanged placeholders and saves a private random Idempotency-Key plus the exact body and challenge in `state.json` (0600). Do not post this file in an issue.

## 6. Authorize with your buyer, then submit explicitly

Use a compatible x402 v2 buyer wallet under its own approval process to authorize the saved request and challenge. Verify the exact price, Base USDC contract, canonical resource and merchant `payTo` against your user's authorization. Save its base64 `PAYMENT-SIGNATURE` header to `.local/example-purchase/payment.txt`, mode 0600. This example does not generate that signature or ask for a private key. Compatible buyer integration is documented in the [official x402 SDK repository](https://github.com/x402-foundation/x402) and the [official Binance Agentic Wallet x402 skill reference](https://github.com/binance/binance-skills-hub/blob/main/skills/binance-web3/binance-agentic-wallet/references/x402-payment.md); follow that buyer's approval flow, network support and spending limits. A synthetic JSON payload or the example inputs are not a usable payment authorization.

```sh
chmod 600 .local/example-purchase/payment.txt
# Replace APPROVED_MERCHANT_ADDRESS with the full address you independently reviewed.
python3 examples/client.py submit --state .local/example-purchase/state.json \
  --payment-file .local/example-purchase/payment.txt \
  --expected-pay-to APPROVED_MERCHANT_ADDRESS
```

This is a **dry run with no HTTP submission**. Only after buyer approval, add `--send` to the same command to submit the existing authorization. This can settle 0.02 Base USDC. The signed header, key and request remain private; the client stores each response and `PAYMENT-RESPONSE` in a new private file rather than printing the signature.

The client freezes the original body/key/authorization before its first send and refuses a replacement payment for that state. It does not independently verify the signature cryptographically; the wallet approval and service/facilitator verification are still required. Customer eligibility, evidence quality, confirmation depth, fee readiness and policy checks still apply per request.

## 7. Retrieve or recover the same purchase

Retry the same submit command with the **same state, exact original body, Idempotency-Key and original authorization**. Do not run `prepare` again, generate a fresh key or sign another payment to repair a timeout. Settled requests return their stored report without a second charge, subject to eligibility checks. A `200` response is a delivered report; save it locally.

| Status | Meaning / next step |
|---|---|
| 400 | Invalid or unsupported input; no new settlement. Check the schema. |
| 402 | Payment terms or failed verification; not proof of a charge. |
| 403 | Eligibility/network/published-address restriction; use support for disputes or classification errors. |
| 409 | Conflict/in-progress; preserve the original purchase and investigate. |
| 425 | Evidence pending, reorganized, stale or insufficiently confirmed; no settlement for that response. |
| 428 | Private random Idempotency-Key missing. |
| 429 | Rate limit; observe Retry-After and keep the original purchase. |
| 502 / 503 / timeout | Evidence unavailable, dependency unavailable or settlement unknown. Preserve the original authorization; a new signature can create a duplicate payment. |

A report showing a confirmed revert or unmet receipt minimum may still be charged because the evidence is the delivered product. No refund or asset transfer is initiated automatically. Contact support with the report ID; never disclose the private key, Idempotency-Key or payment authorization publicly.

## Verification scope

The two free commands and anonymous paid challenges can be checked on live HTTPS without funds. Paid client recovery and safety checks are tested with an isolated HTTP fixture; official SDK payment integration uses a simulated chain. A real independent buyer's mainnet payment and paying demand have not yet been verified. These examples do not claim otherwise.
