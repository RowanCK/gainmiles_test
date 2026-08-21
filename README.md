# GainMiles order data transfer middleware

This repository contains my solution for the GainMiles Python online test.

The source data comes from a legacy order system where field names are abbreviated and values are stored as strings. The program transforms each order into the format required by three downstream consumers:

- Shipping
- Billing
- Notification / Email

Each consumer has its own validation rules. A failure for one consumer does not stop the same order from being processed for the others.

## Project structure

```text
.
├── solution.py
├── test_solution.py
├── requirements-dev.txt
├── .gitignore
└── README.md
```

`solution.py` contains the source dataset, transformation helpers, the three service-specific transformers, and the batch processing function.

`test_solution.py` contains unit tests for the transformation rules and failure-isolation behavior.

## Requirements

- Python 3.9 or later
- pytest for running tests

Create and activate a virtual environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the test dependency:

```bash
python -m pip install -r requirements-dev.txt
```

## Run the solution

```bash
python solution.py
```

The program processes all 10 source orders and prints JSON containing successful transformations and errors for each downstream service.

With the supplied dataset, the expected totals are:

| Service | Successful | Errors |
| --- | ---: | ---: |
| Shipping | 8 | 2 |
| Billing | 7 | 3 |
| Notification | 10 | 0 |

The errors come from the intentionally incomplete or unknown values in the source data:

- `ORD1007`: Billing rejects the order because `amt` is missing.
- `ORD1008`: Shipping rejects the order because `ship_ctry` is missing.
- `ORD1009`: Shipping rejects it for the missing country and Billing rejects it for the missing amount. Notification still succeeds.
- `ORD1010`: Billing rejects the unknown status code `5`.

## Run the tests

```bash
pytest -q
```

The tests cover the normal transformations as well as the main edge cases in the assessment, including:

- PAID and non-PAID shipping behavior
- required shipping country
- USD conversion to cents
- JPY, which has no minor units
- missing and malformed amounts
- unknown billing status
- legacy date parsing
- first-name extraction from `LASTNAME, FIRSTNAME`
- missing notification email
- optional customer name
- isolation when one or more downstream transformations fail

## Implementation notes

### Service-specific transformation

I kept the three target formats separate:

```python
transform_shipping(order)
transform_billing(order)
transform_notification(order)
```

This avoids applying one service's validation rules to another service.

For example, Billing requires `amt`, but Notification does not. If an order is missing its amount, Billing can reject it while Notification can still produce a valid email payload.

### Failure isolation

`process_orders()` runs each order through each transformer independently.

Expected data problems raise `TransformationError`. The processing loop catches that specific exception and records the error under the affected service. It does not catch every possible Python exception, because unexpected programming errors should still surface instead of being silently classified as bad source data.

### Money handling

The legacy system stores monetary values as strings. I use `Decimal` rather than `float` when converting them.

Currencies are mapped to their number of minor units:

```text
USD -> 2
EUR -> 2
GBP -> 2
JPY -> 0
```

Examples:

```text
1299.50 USD -> 129950
7800 JPY    -> 7800
```

This matters for JPY because multiplying every amount by 100 would produce an incorrect result.

### Status mapping

The known legacy status codes are:

```text
1 -> PAID
2 -> PENDING
9 -> CANCELLED
```

Billing needs a normalized status value, so an unknown status is rejected.

Shipping has a narrower rule: an order is shippable only when the source status is `1` (PAID). Other status values therefore produce `shippable: false`.

### Date parsing

Billing converts legacy dates from `YYYYMMDD` to ISO `YYYY-MM-DD`.

For example:

```text
20240115 -> 2024-01-15
```

Invalid dates raise `TransformationError`.

### Notification names

The notification payload derives `first_name` from the supplied `LASTNAME, FIRSTNAME` format.

Examples:

```text
SMITH, JOHN      -> JOHN
LEE, ANNA MARIE  -> ANNA
```

Email is the only required notification field. If the name cannot be derived, the notification can still be produced without `first_name`.

## Scope and assumptions

This solution focuses on transformation and per-service failure handling.

The assessment does not provide network endpoints, authentication details, retry requirements, or a transport such as HTTP or a message queue. For that reason, the code prepares the downstream payloads but does not invent a delivery mechanism.

The currency table contains the currencies present in the supplied source data. Unsupported currencies are rejected rather than guessed.

The source name parser follows the format stated in the assessment. A production system with international name formats would need a different contract instead of relying on comma-separated names.

## AI usage

AI assistance was used during development, as permitted by the assessment instructions. I reviewed and ran the implementation and tests locally. The required conversation log is submitted separately.
