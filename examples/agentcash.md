# Receipt evidence for an existing AgentCash workflow

Use this when a merchant, wallet agent or support tool already has a Base USDC transaction to investigate. This is read-only receipt evidence, not invoice reservation, fraud certification or proof of fulfillment.

## Inspect the result without a wallet or payment

```sh
curl --fail-with-body https://coins.zhidun.ai/demo/usdc-receipt.json
```

This reads one fixed historical public transaction. It accepts no caller transaction parameters. Check `sampleOnly: true`, `notPaymentForThisService: true` and `paymentAttempted: false`. The returned `report` has the same shape as the paid USDC report and is cached for at most five minutes. It is not a customer checkout test.

## Existing AgentCash users: discover and check first

The official CLI documents these inspection commands:

```sh
npx agentcash discover https://coins.zhidun.ai
npx agentcash check https://coins.zhidun.ai/api/v1/payments/usdc-receipt
```

Discovery and schema inspection do not authorize a purchase. Read the returned input/output fields and current price. This guide does not install a wallet or change your agent configuration. AgentCash is a separate buyer; Coins never receives its wallet key.

## For your own transaction

1. Obtain the authorized transaction hash and recipient. Select the expected token payer if needed; it may differ from the gas-paying relayer.
2. Read the live terms and declare the actual eligible customer's country. Paid services are offered only to actual customers outside mainland China, where lawful. Do not infer the country from an agent's server.
3. Save one exact request body and a private random `Idempotency-Key` of 24–128 characters. Use a different key per service and purchase. Our standard-library client can prepare these private files; see [README.md](README.md).
4. After the buyer explicitly approves the current 0.02 Base USDC terms, use its structured fetch tool to POST the saved body and original key to the receipt endpoint. AgentCash's documented request interface supports method, body and headers. It can handle x402 payment; funded end-to-end compatibility with this service is still a separate test. Never provide Coins a private key or seed phrase.
5. Inspect `minimumReceivedMet`, `matchedReceivedRaw`, `matchedTransfers` and confirmation depth. Do not release a new invoice solely because an unrelated old transfer exists. Keep an application ledger that binds receipts to invoices.
6. If a request is interrupted or settlement is unknown, preserve the original body, key and payment authorization. Do not let automatic troubleshooting create a second authorization. Resolve/retrieve the original purchase before making another.

AgentCash documents `--max-amount 0.02` as a payment ceiling for CLI fetches. That flag alone is not purchase consent and does not enforce our body/key recovery rules. The safer first step is schema inspection and the free fixed example. Do not put a private retrieval key or signed payment in a public issue, command transcript or chat.

Paid price remains 0.02 USDC per delivered report. The reports rely on one RPC; Base L2 depth is not Ethereum L1 finality, and reported gas does not total every possible fee component. No mainnet buyer success, independent customer result or availability SLA is implied by this guide.

References, checked 23 October 2026: [AgentCash CLI interface](https://agentcash.dev/docs/cli/fetch), [discovery workflow](https://agentcash.dev/docs/discovering-endpoints), [live schema](https://coins.zhidun.ai/openapi.json), [service terms](https://coins.zhidun.ai/privacy.html).
