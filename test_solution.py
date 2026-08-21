import pytest
from solution import (
    TransformationError,
    amount_to_minor_units,
    transform_billing,
    transform_shipping,
)


def test_transform_shipping():
    order = {
        "ord_no": "ORD1001",
        "cust_nm": "SMITH, JOHN",
        "ship_ctry": "US",
        "gift_flag": "Y",
        "status": "1",
    }

    result = transform_shipping(order)

    assert result == {
        "order_id": "ORD1001",
        "recipient": "SMITH, JOHN",
        "country": "US",
        "is_gift": True,
        "shippable": True,
    }


def test_shipping_pending_order_is_not_shippable():
    order = {
        "ord_no": "ORD1003",
        "cust_nm": "CHEN, WEI",
        "ship_ctry": "US",
        "gift_flag": "N",
        "status": "2",
    }

    result = transform_shipping(order)

    assert result["is_gift"] is False
    assert result["shippable"] is False


def test_shipping_requires_country():
    order = {
        "ord_no": "ORD1008",
        "cust_nm": "MUELLER, HANS",
        "ship_ctry": "",
        "gift_flag": "N",
        "status": "1",
    }

    with pytest.raises(
        TransformationError,
        match="Missing shipping country",
    ):
        transform_shipping(order)

def test_billing_usd_amount():
    order = {
        "ord_no": "ORD1001",
        "amt": "1299.50",
        "ccy": "USD",
        "ord_dt": "20240115",
        "status": "1",
    }

    result = transform_billing(order)

    assert result == {
        "invoice": {
            "order_id": "ORD1001",
            "amount_cents": 129950,
            "currency": "USD",
        },
        "placed_at": "2024-01-15",
        "status": "PAID",
    }


def test_billing_jpy_has_no_minor_units():
    assert amount_to_minor_units("7800", "JPY") == 7800


def test_billing_requires_amount():
    order = {
        "ord_no": "ORD1007",
        "amt": "",
        "ccy": "EUR",
        "ord_dt": "20240405",
        "status": "2",
    }

    with pytest.raises(
        TransformationError,
        match="Missing amount",
    ):
        transform_billing(order)


def test_billing_rejects_unknown_status():
    order = {
        "ord_no": "ORD1010",
        "amt": "300.00",
        "ccy": "USD",
        "ord_dt": "20240420",
        "status": "5",
    }

    with pytest.raises(
        TransformationError,
        match="Unknown status code: 5",
    ):
        transform_billing(order)
