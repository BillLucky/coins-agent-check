# Coins Agent Check

**Paid alpha — 22 October 2026:** Three report services accept per-report x402 payments when live dependencies are ready; two deterministic tools remain free. Check `/healthz` and `/api/v1/services` before buying. Reports are saved before settlement and identical paid requests retrieve their original report without a second charge.

Read-only payment and token evidence for AI agents. Public alpha. Paid reports are offered only to actual customers outside mainland China, where lawful and subject to applicable sanctions. Public pages, discovery and the two deterministic free tools remain accessible.

**Live gateway: https://coins.zhidun.ai/**

**For merchants and wallet agents investigating Base USDC receipts:** [run a free public-chain example](https://coins.zhidun.ai/?ref=github#receipt-demo) before integrating. It reads one fixed historical transaction, accepts no caller input and makes no payment. Then use the [merchant/AgentCash workflow](examples/agentcash.md) for your own authorized input at 0.02 USDC per report. Receipt evidence is separate from invoice uniqueness and fulfillment.

- [Agent skill](SKILL.md) · [OpenAPI](openapi.json) · [Live service catalog](https://coins.zhidun.ai/api/v1/services)
- [x402scan](https://www.x402scan.com/server/2e5afbfc-fdbd-4058-8534-0ec674db5375) · [Health](https://coins.zhidun.ai/healthz)
- [Runnable examples](examples/README.md) · [Live example overview](https://coins.zhidun.ai/examples.html)
- [Receipt and retry integration notes](INTEGRATION_NOTES.md) · [Privacy and service terms](https://coins.zhidun.ai/privacy.html)

For an exact x402scan lookup, open [All](https://www.x402scan.com/all) and enter `zhidun.ai`, or use the direct listing above. Checked on 23 October 2026: the listing contains all five tools plus the legacy free route. The Discover homepage uses a usage-filtered semantic search, so it is not a complete domain lookup and registration does not guarantee recommendation visibility. The live catalog and schema remain authoritative for availability.

## Tools

| POST path | Price | Result |
| --- | --- | --- |
| `/api/v1/costs/preflight` | Free | Exact-decimal cost math and quote-age flags from your assumptions |
| `/api/v1/evm/calldata` | Free | Canonical ERC-20 approve / transfer / transferFrom parameter interpretation |
| `/api/v1/payments/usdc-receipt` | 0.02 USDC on Base | Base USDC Transfer evidence against a recipient, optional payer and minimum |
| `/api/v1/tokens/allowances` | 0.02 USDC on Base | One-block balance and allowance evidence for up to three spenders on BSC or Base |
| `/v1/bsc/reconcile` | 0.02 USDC on Base | Canonical BSC receipt, gas, ERC-20 event net flows and declared minimum receipts |

The legacy free `/v1/preflight` remains available. BSC reports read chain 56; Base reports read chain 8453. **All payments use Base USDC.** No private keys, exchange credentials or wallet sessions are accepted.

## Integrate

Start with `python3 examples/client.py demo`, `python3 examples/client.py cost` or `python3 examples/client.py calldata`. Three `challenge --service ...` commands inspect paid terms without buying. The [full walkthrough](examples/README.md) includes real-input templates, private preparation, an explicit authorized-submit step and recovery of the original purchase. No private key is accepted, and submission is a dry run until `--send` is passed.

Read [SKILL.md](SKILL.md) and the current live schema. For an eligible network, an empty POST to a paid resource returns its x402 v2 terms without buying a report:

```sh
curl -i -X POST https://coins.zhidun.ai/api/v1/payments/usdc-receipt
```

Before using an approved compatible buyer, verify the amount, asset, network, recipient and resource URL against your authorization. Use a separate private random `Idempotency-Key` for each service and new purchase. Preserve the exact body, key and original payment authorization across retries; never sign another payment to repair an unknown settlement. Successful duplicate requests retrieve the original report, including when the live chain/payment upstream is unavailable, subject to current eligibility controls.

A restricted network receives `X-Coins-Paid-Access: region-restricted` and paid calls return JSON `403 region_not_supported` before settlement. `check-eligibility` and global `paymentsReady` do not establish actual customer eligibility. See the service terms and contact support about a network classification error.

New paid inputs require truthful `customerCountryCode` and `termsAccepted: true`. Legacy BSC inputs use `X-Customer-Country` and `X-Terms-Accepted: true` headers. The actual customer's location determines eligibility; Agent hosting does not. Example countries and addresses must be replaced with real authorized input.

## Coverage and verification status

BSC receipt depth is at least 12 confirmations; Base USDC receipt depth is at least 20 L2 confirmations, which is not Ethereum L1 finality. Reported Base gas is the execution component, not a verified total of every fee. Allowance readings are permissions under standard ERC-20 semantics, not a prediction of loss. ABI interpretation is not simulation or a contract audit. Paid results rely on a single RPC, with explicit failure and reorganization checks; public upstreams have no purchased SLA.

Unsupported input, pending transactions and unavailable evidence are not settled. A completed report showing a revert or an unmet receipt minimum may be charged because the evidence itself is the product. See the skill for conflicts, unknown payments and eligibility restrictions.

Offline payment-boundary tests, direct read-only BSC/Base evidence, public challenges and invalid-signature refusal have been checked. **A valid independent buyer's mainnet payment and paying demand have not yet been verified.** This is an alpha, without a production SLA or promised customer results. Directory acceptance is separate from quality endorsement or revenue.

Use the homepage inquiry form for a redacted workflow or integration question. Never post a private idempotency key or payment authorization. This repository contains integration documentation; the live API is authoritative for current schema, price and readiness. This is an independent service, not an official Binance product or partnership.
