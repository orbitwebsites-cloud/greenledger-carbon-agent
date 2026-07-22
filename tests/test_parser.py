from datetime import date

import pytest

from greenledger.parser import BillParseError, parse_bill_text

ELECTRICITY_TEXT = """
Garden State Power & Light
123 Utility Plaza, Springfield, NJ 07081

ELECTRICITY BILL

Customer: Patel Household
Service Address: 142 Maple St, Springfield, NJ 07081
Account Number: ELE-88340219

Billing Period: 2026-07-01 to 2026-07-31
Usage: 1044.3 kWh
Amount Due: $182.75

Thank you for being a valued customer.
"""

GAS_TEXT = """
Jersey Natural Gas Co.
GAS BILL
Account Number: GAS-55210873
Billing Period: 2026-01-01 to 2026-01-31
Usage: 92.4 therms
Amount Due: $124.74
"""

WATER_TEXT = """
Springfield Municipal Water
WATER BILL
Account Number: WTR-91002234
Billing Period: 2026-06-01 to 2026-06-30
Usage: 5250.0 gallons
Amount Due: $49.88
"""


def test_parse_electricity_bill():
    bill = parse_bill_text(ELECTRICITY_TEXT, source_file="electricity_2026-07.pdf")
    assert bill.utility_type == "electricity"
    assert bill.usage == pytest.approx(1044.3)
    assert bill.unit == "kwh"
    assert bill.period_start == date(2026, 7, 1)
    assert bill.period_end == date(2026, 7, 31)
    assert bill.account_number == "ELE-88340219"


def test_parse_gas_bill():
    bill = parse_bill_text(GAS_TEXT, source_file="gas_2026-01.pdf")
    assert bill.utility_type == "natural_gas"
    assert bill.usage == pytest.approx(92.4)
    assert bill.unit == "therms"


def test_parse_water_bill():
    bill = parse_bill_text(WATER_TEXT, source_file="water_2026-06.png")
    assert bill.utility_type == "water"
    assert bill.usage == pytest.approx(5250.0)


def test_missing_usage_raises():
    with pytest.raises(BillParseError):
        parse_bill_text("Not a bill at all", source_file="junk.pdf")


def test_missing_billing_period_raises():
    text = "ELECTRICITY BILL\nUsage: 500 kWh\n"
    with pytest.raises(BillParseError):
        parse_bill_text(text, source_file="broken.pdf")


def test_utility_type_falls_back_to_unit_when_header_missing():
    text = (
        "Some Utility Co\n"
        "Account Number: X-1\n"
        "Billing Period: 2026-02-01 to 2026-02-28\n"
        "Usage: 400 kWh\n"
    )
    bill = parse_bill_text(text, source_file="noheader.pdf")
    assert bill.utility_type == "electricity"
