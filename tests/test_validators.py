"""Runs the 10 assignment test cases through the validators."""
import pytest

import validators as v

# (test#, name, dob, email, glucose, hb, chol, expected_error_fields)
CASES = [
    (1, "Robyn Pears", "28.01.1960", "robyn@gmail.com", "232", "13.5", "180", set()),
    (2, "John Hunter", "10.12.1990", "hunter@gmail", "94", "15", "200", {"email"}),
    (3, "Darryl Tim", "12.11.1993", "timd@smh.com.au", "240", "18.6", "326", set()),
    (4, "Peter Larry", "31.11.2001", "Larry@hotmail.com", "88", "11.5", "165", {"dob"}),
    (5, "Sam Kerr", "09.12.2006", "sam@news.com.au", "198", "8.9", "192", set()),
    (7, "Madison XI", "12.09.1998", "madison@hotmail.com", "85", "7.6", "163", set()),
    (8, "Kris Wu", "19.10.2030", "Kris.wu.gmail.com", "79", "16.5", "197", {"dob", "email"}),
    (9, "Tenille Singh", "30.11.1991", "Tenille@yahoo.com", "101", "15", "310", set()),
    (10, "Prem Kumar", "28.04.1990", "prem@telstra.com", "155", "12.5", "265", set()),
]


@pytest.mark.parametrize("num,name,dob,email,glu,hb,chol,expected", CASES)
def test_assignment_cases(num, name, dob, email, glu, hb, chol, expected):
    result = v.validate_patient(name, dob, email, glu, hb, chol)
    assert set(result.errors) == expected


def test_dob_normalised_to_slashes():
    assert v.validate_dob("28.01.1960") == "28/01/1960"


def test_non_numeric_blood_values():
    result = v.validate_patient("A Person", "01/01/1990", "a@b.com", "abc", "", "12x")
    assert set(result.errors) == {"glucose", "haemoglobin", "cholesterol"}
