import pytest

from solution import TransformationError, transform_shipping


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