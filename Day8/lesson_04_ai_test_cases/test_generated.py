from main import app

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Each table row sends one independent request; no external server is needed."""
    with TestClient(app) as test_client:
        yield test_client


# Expected values are derived from the business contract, not the implementation.
@pytest.mark.parametrize(
    "amount, expected",
    [
        pytest.param(5000, {"amount": 5000, "discount": 0, "payable": 5000}, id="N01"),
        pytest.param(20000, {"amount": 20000, "discount": 1000, "payable": 19000}, id="N02"),
        pytest.param(1, {"amount": 1, "discount": 0, "payable": 1}, id="E01"),
        pytest.param(100000, {"amount": 100000, "discount": 1000, "payable": 99000}, id="E02"),
        pytest.param(9999, {"amount": 9999, "discount": 0, "payable": 9999}, id="R01"),
        pytest.param(10000, {"amount": 10000, "discount": 1000, "payable": 9000}, id="R02"),
        pytest.param(10001, {"amount": 10001, "discount": 1000, "payable": 9001}, id="R03"),
    ],
)
def test_quote_success(client, amount, expected):
    response = client.post("/quotes", json={"amount": amount})

    assert response.status_code == 200
    actual = response.json()
    assert actual == expected
    # Python considers True == 1 and 1.0 == 1; verify JSON value types too.
    assert all(type(actual[field]) is int for field in expected)


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"amount": 0}, id="B01"),
        pytest.param({"amount": 100001}, id="B02"),
        pytest.param({}, id="M01"),
        pytest.param({"amount": "10000"}, id="T01"),
        pytest.param({"amount": 10000.0}, id="T02"),
        pytest.param({"amount": 10000.5}, id="T03"),
        pytest.param({"amount": True}, id="T04"),
        pytest.param({"amount": False}, id="T05"),
        pytest.param({"amount": None}, id="T06"),
        pytest.param({"amount": []}, id="T07"),
        pytest.param({"amount": {}}, id="T08"),
    ],
)
def test_quote_invalid(client, body):
    response = client.post("/quotes", json=body)

    assert response.status_code == 422
    # The business contract does not specify an error body schema or message.
