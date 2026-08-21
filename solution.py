import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional


orders = [
    {
        "ord_no": "ORD1001",
        "cust_nm": "SMITH, JOHN",
        "ord_dt": "20240115",
        "amt": "1299.50",
        "ccy": "USD",
        "ship_ctry": "US",
        "cust_email": "john.smith@example.com",
        "gift_flag": "Y",
        "status": "1",
    },
    {
        "ord_no": "ORD1002",
        "cust_nm": "GARCIA, MARIA",
        "ord_dt": "20240220",
        "amt": "89.00",
        "ccy": "EUR",
        "ship_ctry": "ES",
        "cust_email": "maria.garcia@example.com",
        "gift_flag": "N",
        "status": "1",
    },
    {
        "ord_no": "ORD1003",
        "cust_nm": "CHEN, WEI",
        "ord_dt": "20240305",
        "amt": "450.75",
        "ccy": "USD",
        "ship_ctry": "US",
        "cust_email": "wei.chen@example.com",
        "gift_flag": "N",
        "status": "2",
    },
    {
        "ord_no": "ORD1004",
        "cust_nm": "O'BRIEN, SEAN",
        "ord_dt": "20240312",
        "amt": "1500.00",
        "ccy": "GBP",
        "ship_ctry": "GB",
        "cust_email": "sean.obrien@example.com",
        "gift_flag": "Y",
        "status": "9",
    },
    {
        "ord_no": "ORD1005",
        "cust_nm": "LEE, ANNA MARIE",
        "ord_dt": "20240318",
        "amt": "230.00",
        "ccy": "USD",
        "ship_ctry": "US",
        "cust_email": "anna.lee@example.com",
        "gift_flag": "N",
        "status": "1",
    },
    {
        "ord_no": "ORD1006",
        "cust_nm": "TANAKA, KENJI",
        "ord_dt": "20240401",
        "amt": "7800",
        "ccy": "JPY",
        "ship_ctry": "JP",
        "cust_email": "kenji.tanaka@example.com",
        "gift_flag": "N",
        "status": "1",
    },
    {
        "ord_no": "ORD1007",
        "cust_nm": "DUBOIS, CLAIRE",
        "ord_dt": "20240405",
        "amt": "",
        "ccy": "EUR",
        "ship_ctry": "FR",
        "cust_email": "claire.dubois@example.com",
        "gift_flag": "N",
        "status": "2",
    },
    {
        "ord_no": "ORD1008",
        "cust_nm": "MUELLER, HANS",
        "ord_dt": "20240410",
        "amt": "99.99",
        "ccy": "EUR",
        "ship_ctry": "",
        "cust_email": "hans.mueller@example.com",
        "gift_flag": "N",
        "status": "1",
    },
    {
        "ord_no": "ORD1009",
        "cust_nm": "ROSSI, GIULIA",
        "ord_dt": "20240415",
        "amt": "",
        "ccy": "EUR",
        "ship_ctry": "",
        "cust_email": "giulia.rossi@example.com",
        "gift_flag": "N",
        "status": "1",
    },
    {
        "ord_no": "ORD1010",
        "cust_nm": "KIM, MINJUN",
        "ord_dt": "20240420",
        "amt": "300.00",
        "ccy": "USD",
        "ship_ctry": "KR",
        "cust_email": "minjun.kim@example.com",
        "gift_flag": "N",
        "status": "5",
    },
]


class TransformationError(Exception):
    """Raised when an order cannot be transformed for a downstream service."""

    pass


class Status(Enum):
    PAID = "PAID"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"


STATUS_MAP = {
    "1": Status.PAID,
    "2": Status.PENDING,
    "9": Status.CANCELLED,
}


CURRENCY_MINOR_UNITS = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,
}


def parse_status(status_code: str) -> Status:
    try:
        return STATUS_MAP[status_code]
    except KeyError:
        raise TransformationError(
            f"Unknown status code: {status_code}"
        )


def parse_date(date_str: str) -> str:
    try:
        return datetime.strptime(
            date_str,
            "%Y%m%d",
        ).date().isoformat()
    except ValueError:
        raise TransformationError(
            f"Invalid order date: {date_str}"
        )


def amount_to_minor_units(amount: str, currency: str) -> int:
    if not amount:
        raise TransformationError("Missing amount")

    if currency not in CURRENCY_MINOR_UNITS:
        raise TransformationError(
            f"Unsupported currency: {currency}"
        )

    try:
        decimal_amount = Decimal(amount)
    except InvalidOperation:
        raise TransformationError(
            f"Invalid amount: {amount}"
        )

    minor_units = CURRENCY_MINOR_UNITS[currency]
    multiplier = Decimal(10) ** minor_units

    return int(decimal_amount * multiplier)


def extract_first_name(full_name: str) -> Optional[str]:
    if not full_name or "," not in full_name:
        return None

    _, given_names = full_name.split(",", 1)
    given_names = given_names.strip()

    if not given_names:
        return None

    return given_names.split()[0]


def transform_shipping(order: dict[str, str]) -> dict[str, object]:
    country = order.get("ship_ctry", "").strip()

    if not country:
        raise TransformationError("Missing shipping country")

    return {
        "order_id": order["ord_no"],
        "recipient": order["cust_nm"],
        "country": country,
        "is_gift": order.get("gift_flag") == "Y",
        "shippable": order.get("status") == "1",
    }


def transform_billing(order: dict[str, str]) -> dict[str, object]:
    status = parse_status(order.get("status", ""))

    return {
        "invoice": {
            "order_id": order["ord_no"],
            "amount_cents": amount_to_minor_units(
                order.get("amt", ""),
                order.get("ccy", ""),
            ),
            "currency": order["ccy"],
        },
        "placed_at": parse_date(order["ord_dt"]),
        "status": status.value,
    }


def transform_notification(order: dict[str, str]) -> dict[str, object]:
    email = order.get("cust_email", "").strip()

    if not email:
        raise TransformationError("Missing customer email")

    result = {
        "to": email,
        "locale": "en-US",
    }

    first_name = extract_first_name(
        order.get("cust_nm", "")
    )

    if first_name:
        result["first_name"] = first_name

    return result


def process_orders(
    orders: list[dict[str, str]],
) -> dict[str, dict[str, list[dict[str, object]]]]:
    transformers = {
        "shipping": transform_shipping,
        "billing": transform_billing,
        "notification": transform_notification,
    }

    results = {
        service_name: {
            "success": [],
            "errors": [],
        }
        for service_name in transformers
    }

    for order in orders:
        order_id = order.get("ord_no", "UNKNOWN")

        for service_name, transformer in transformers.items():
            try:
                transformed_order = transformer(order)
            except TransformationError as exc:
                results[service_name]["errors"].append({
                    "order_id": order_id,
                    "error": str(exc),
                })
            else:
                results[service_name]["success"].append(
                    transformed_order
                )

    return results


if __name__ == "__main__":
    results = process_orders(orders)
    print(json.dumps(results, indent=2))