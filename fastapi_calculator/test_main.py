"""실행: python -m unittest -v"""
from decimal import Decimal
import unittest

from fastapi.testclient import TestClient
from main import app, calculate, format_number, parse_number


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_home_and_stylesheet(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="first"', response.text)
        self.assertIn('name="second"', response.text)
        self.assertIn('action="/calculate"', response.text)
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)

    def test_four_operations(self):
        rows = calculate(Decimal("10"), Decimal("2"))
        self.assertEqual([row[2] for row in rows], ["12", "8", "20", "5"])
        page = self.client.get("/calculate", params={"first": "10", "second": "2"})
        self.assertEqual(page.status_code, 200)
        for value in ["12", "8", "20", "5"]:
            self.assertIn(f"<strong>{value}</strong>", page.text)

    def test_exact_decimal_and_negative(self):
        self.assertEqual(calculate(Decimal("0.1"), Decimal("0.2"))[0][2], "0.3")
        self.assertEqual([r[2] for r in calculate(Decimal("-3"), Decimal("2"))], ["-1", "-5", "-6", "-1.5"])

    def test_zero_division_keeps_other_results(self):
        page = self.client.get("/calculate", params={"first": "7", "second": "0"})
        self.assertEqual(page.status_code, 200)
        self.assertIn("0으로 나눌 수 없어요.", page.text)
        self.assertIn("<strong>7</strong>", page.text)
        self.assertIn("<strong>0</strong>", page.text)
        self.assertEqual(calculate(Decimal("0"), Decimal("0"))[0][2], "0")

    def test_division_rounding(self):
        self.assertEqual(calculate(Decimal("1"), Decimal("3"))[3][2], "0.333333333333")
        self.assertEqual(calculate(Decimal("2"), Decimal("3"))[3][2], "0.666666666667")

    def test_invalid_input_returns_readable_error(self):
        for value in ["", "abc", "NaN", "Infinity", "1e3", "1,000", "0.1234567890123", "1000000000001", "-1000000000001"]:
            with self.subTest(value=value):
                response = self.client.get("/calculate", params={"first": value, "second": "2"})
                self.assertEqual(response.status_code, 422)
                self.assertIn('role="alert"', response.text)
        self.assertEqual(self.client.get("/calculate", params={"first": "2"}).status_code, 422)
        self.assertEqual(self.client.get("/calculate", params={"first": "2", "second": "abc"}).status_code, 422)

    def test_boundaries_and_small_divisor(self):
        self.assertEqual(parse_number("1000000000000", "value"), Decimal("1000000000000"))
        self.assertEqual(parse_number(" -0.5 ", "value"), Decimal("-0.5"))
        result = calculate(Decimal("1000000000000"), Decimal("0.000000000001"))
        self.assertEqual(result[3][2], "1000000000000000000000000")
        self.assertEqual(format_number(Decimal("-0.000")), "0")

    def test_html_injection_is_escaped(self):
        attack = '\"><script>alert(1)</script>'
        page = self.client.get("/calculate", params={"first": attack, "second": "2"})
        self.assertEqual(page.status_code, 422)
        self.assertNotIn("<script>", page.text)
        self.assertIn("&lt;script&gt;", page.text)


if __name__ == "__main__":
    unittest.main()
