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
]

class TransformationError(Exception):
    """Raised when an order cannot be transformed for a downstream service."""

    pass

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

if __name__ == "__main__":
    for order in orders:
        print(order)