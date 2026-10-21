# Receipt and retry integration notes

Three mistakes can make an agent's receipt bookkeeping look correct while attributing the wrong payer, overstating finality or charging twice.

## Separate token payer from relayer

An EIP-3009 USDC transfer can be submitted by a relayer. The transaction's `from` address pays gas; it is not necessarily the account transferring USDC. Match the official token contract's Transfer evidence and its `from`, `to` and raw amount against the declared receipt. Do not count self-transfers or logs emitted by a different token as a receipt of the expected asset.

Our Base report makes these fields explicit. It does not identify the customer, reserve an invoice, prevent off-chain invoice reuse or prove fulfillment. A negative finding is still a delivered evidence report.

References: [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009), [Circle's contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).

## State the evidence you actually read

A receipt must agree with its transaction and canonical block. An allowance snapshot should pin the balance and permission calls to the same block and recheck that block's hash. Keep raw amounts as integers; optional token decimals can be unknown.

Maximum uint256 permission is not the same as an immediate loss. Tokens can implement nonstandard view functions, and a matching ABI selector does not establish contract identity or behavior. A report based on one public RPC is not a contract audit or independent consensus verification.

Our Base receipt depth is L2 depth. Its gas field is `gasUsed × effectiveGasPrice`; it does not claim to total every other fee component. Public RPCs can permit a chain-ID lookup while requiring different access for receipts, so probe the method the product actually depends on. A denied or unknown response is not a zero balance or a failed transaction.

## Preserve one purchase across retries

Generate one private random Idempotency-Key per purchase and keep it with the exact body and original payment authorization. This key is also a retrieval capability. Do not place it in a URL, a public issue or analytics.

On an unresolved settlement, resend the original request and authorization. Creating a fresh payment to fix a timeout can create a second charge. Our seller persists the report before attempting settlement and binds the payment nonce and key across products. An already-settled report can be retrieved without a new payment or a live RPC, subject to current eligibility controls.

These are implementation boundaries, not evidence of an independently verified mainnet buyer payment or a service-level guarantee. Start with the two free tools and current schema, then decide whether a paid report solves a real workflow for an eligible customer.
