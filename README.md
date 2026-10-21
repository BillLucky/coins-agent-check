# Coins Agent Check

BSC transaction receipt reconciliation and exact-decimal cost preflight for AI agents. Public alpha, launched 21 October 2026.

**Live service: https://coins.os.zhidun-ai.com/**

- [Current OpenAPI schema](https://coins.os.zhidun-ai.com/openapi.json)
- [Agent skill](SKILL.md)
- [Service manifest](https://coins.os.zhidun-ai.com/.well-known/agent.json)
- [x402 discovery index](https://coins.os.zhidun-ai.com/.well-known/x402)
- [Health](https://coins.os.zhidun-ai.com/healthz)
- [Privacy and service terms](https://coins.os.zhidun-ai.com/privacy.html)

## What you can call

| Operation | Price | Result |
| --- | --- | --- |
| `POST /v1/preflight` | Free | Exact-decimal transaction cost math and quote-age flags from your assumptions |
| `POST /v1/bsc/reconcile` | 0.02 USDC on Base per delivered report | Canonical BSC receipt check, gas, ERC-20 event net flows and expected minimum receipts |

Reports analyze **BSC (56)**. Payments use **Base (8453)**. No private keys, exchange credentials or wallet sessions are submitted to the service.

## Integrate

Read the current schema and [SKILL.md](SKILL.md). Make an unpaid request to inspect x402 v2 payment terms. Before signing, verify the amount, asset, network and recipient against your authorization. Use your approved compatible buyer wallet.

The paid route needs a private random `Idempotency-Key`, such as a UUID. Preserve it with the exact body and payment authorization across retries. Successful duplicate requests retrieve the same report. Do not sign a second payment to fix a timeout or an unresolved settlement.

Invalid inputs, unknown/pending BSC transactions, insufficient confirmations and unavailable evidence are not settled. A confirmed reverted transaction can produce a paid report of its revert and gas. The report covers receipt events, not internal transfers, token authenticity, prices or a full balance audit.

## Quick discovery probe (no payment)

```sh
curl -i -X POST https://coins.os.zhidun-ai.com/v1/bsc/reconcile
```

This returns `402 Payment Required` and a machine-readable challenge. It does not submit a transaction or pay for a report.

## Feedback and integrations

Use the inquiry form on the homepage. Useful feedback includes a redacted workflow, which result you need and which integrations consume it. Never publish a private idempotency key or payment authorization in an issue.

This public repository contains integration documentation. The live API is authoritative for current schema, price and availability. This is an independent service, not an official Binance product. Registry indexing and paying customer demand are separate from API availability.
