"""Input validation for patient records. Pure functions - no UI or DB code."""
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime

import config

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,99}$")
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")

FIELD_LABELS = {
    "glucose": "Glucose",
    "haemoglobin": "Haemoglobin",
    "cholesterol": "Cholesterol",
}


@dataclass
class ValidationResult:
    errors: dict = field(default_factory=dict)   # field name -> message
    cleaned: dict = field(default_factory=dict)  # normalised values (only when valid)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_name(value: str) -> str:
    value = " ".join((value or "").split())
    if not value:
        raise ValueError("Full name is required.")
    if not NAME_RE.match(value):
        raise ValueError("Full name may contain only letters, spaces, '.', '-' and apostrophes (min 2 characters).")
    return value


def validate_dob(value: str) -> str:
    """Return the DOB normalised to dd/mm/yyyy, or raise ValueError."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Date of birth is required.")
    # Accept '.' and '-' as separators and store everything as dd/mm/yyyy
    normalised = value.replace(".", "/").replace("-", "/")
    if not DATE_RE.match(normalised):
        raise ValueError("Date of birth must be in dd/mm/yyyy format.")
    try:
        parsed = datetime.strptime(normalised, config.DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"'{value}' is not a real calendar date (e.g. 31/11 does not exist).") from None
    today = date.today()
    if parsed > today:
        raise ValueError("Date of birth cannot be in the future.")
    if (today.year - parsed.year) > config.MAX_AGE_YEARS:
        raise ValueError(f"Date of birth is more than {config.MAX_AGE_YEARS} years ago.")
    return parsed.strftime(config.DATE_FORMAT)


def validate_email(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError("Email address is required.")
    if not EMAIL_RE.match(value):
        raise ValueError("Email address is not in a valid format (e.g. name@example.com).")
    return value


def validate_measurement(key: str, value) -> float:
    label = FIELD_LABELS[key]
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"{label} must be a number.") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a valid number.")
    low, high = config.RANGES[key]
    if not low <= number <= high:
        raise ValueError(f"{label} must be between {low:g} and {high:g}.")
    return number


def calculate_age(dob_text: str) -> int:
    dob = datetime.strptime(dob_text, config.DATE_FORMAT).date()
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def validate_patient(full_name, dob, email, glucose, haemoglobin, cholesterol) -> ValidationResult:
    """Validate every field and collect ALL errors (not just the first)."""
    result = ValidationResult()
    checks = {
        "full_name": lambda: validate_name(full_name),
        "dob": lambda: validate_dob(dob),
        "email": lambda: validate_email(email),
        "glucose": lambda: validate_measurement("glucose", glucose),
        "haemoglobin": lambda: validate_measurement("haemoglobin", haemoglobin),
        "cholesterol": lambda: validate_measurement("cholesterol", cholesterol),
    }
    for key, check in checks.items():
        try:
            result.cleaned[key] = check()
        except ValueError as exc:
            result.errors[key] = str(exc)
    if result.errors:
        result.cleaned = {}
    return result
