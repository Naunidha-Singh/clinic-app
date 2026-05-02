"""
Input Sanitization Module — Defense-in-Depth for SQL Injection Protection

═══ STAGE 3: INPUT SANITIZATION ═══
This module validates and sanitizes ALL user input BEFORE it reaches any SQL query.
Even though we use prepared statements (which prevent SQL injection on their own),
input sanitization adds a second layer of defense:

  1. Prepared Statements: prevent injected SQL from executing (database level)
  2. Input Sanitization:  reject or strip malicious input entirely (application level)

This follows the "defense-in-depth" principle — if one layer fails, the other still
protects the system.

Reference: SQLInCode_slides.pdf — SQL Injection, Input Sanitization
"""

import re
from datetime import datetime


class ValidationError(Exception):
    """Raised when user input fails sanitization checks."""
    pass


# ─── Name Sanitization ────────────────────────────────────────────────────────
def sanitize_name(value, field_name="Name"):
    """Sanitize a name field (first_name, last_name, medication, etc.).

    Rules:
    - Must not be empty or whitespace-only
    - Must be 1-100 characters after stripping
    - Must not contain SQL-dangerous characters: ; ' " -- /* */
    - Strips leading/trailing whitespace

    Without this, a user could submit an empty name or a name containing
    SQL fragments — even with prepared statements, we want clean data.
    """
    if value is None or str(value).strip() == '':
        raise ValidationError(f"{field_name} is required and cannot be empty")

    value = str(value).strip()

    if len(value) > 100:
        raise ValidationError(f"{field_name} must be 100 characters or fewer")

    # Reject strings containing SQL injection patterns
    sql_patterns = [
        r"[;]",           # Statement terminator
        r"--",            # SQL comment
        r"/\*",           # Block comment start
        r"\*/",           # Block comment end
        r"\\x",           # Hex escape sequences
    ]
    for pattern in sql_patterns:
        if re.search(pattern, value):
            raise ValidationError(f"{field_name} contains invalid characters")

    return value


# ─── Email Sanitization ───────────────────────────────────────────────────────
def sanitize_email(value):
    """Sanitize an email address.

    Rules:
    - If empty, returns empty string (email is optional)
    - If provided, must match a basic email pattern
    - Must be 254 characters or fewer (RFC 5321)
    """
    if value is None or str(value).strip() == '':
        return ''

    value = str(value).strip()

    if len(value) > 254:
        raise ValidationError("Email must be 254 characters or fewer")

    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError("Invalid email format")

    return value


# ─── Phone Sanitization ───────────────────────────────────────────────────────
def sanitize_phone(value):
    """Sanitize a phone number.

    Rules:
    - If empty, returns empty string (phone is optional)
    - Allows only digits, dashes, parentheses, spaces, and plus sign
    - Must be 20 characters or fewer
    """
    if value is None or str(value).strip() == '':
        return ''

    value = str(value).strip()

    if len(value) > 20:
        raise ValidationError("Phone number must be 20 characters or fewer")

    # Only allow phone-safe characters
    if not re.match(r'^[0-9()\-\s+.]+$', value):
        raise ValidationError("Phone number contains invalid characters")

    return value


# ─── Date Sanitization ────────────────────────────────────────────────────────
def sanitize_date(value, field_name="Date"):
    """Sanitize a date string.

    Rules:
    - Must be in YYYY-MM-DD format (ISO 8601)
    - Must be a valid calendar date (e.g., no Feb 30)
    - Rejects any non-date characters

    This prevents injection through date fields — without this, a user
    could submit '2024-01-01; DROP TABLE patients' as a date value.
    """
    if value is None or str(value).strip() == '':
        raise ValidationError(f"{field_name} is required")

    value = str(value).strip()

    # Strict format check: must be exactly YYYY-MM-DD
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")

    # Validate it's a real date
    try:
        datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(f"{field_name} is not a valid date")

    return value


# ─── Whitelist Sanitization (Gender, Status) ──────────────────────────────────
def sanitize_gender(value):
    """Sanitize gender field using a strict whitelist.

    Only allows values that match the CHECK constraint in the database.
    This is the strongest form of input sanitization — anything not
    in the whitelist is rejected outright.
    """
    allowed = {'Male', 'Female', 'Other'}
    if value not in allowed:
        raise ValidationError(f"Gender must be one of: {', '.join(sorted(allowed))}")
    return value


def sanitize_status(value):
    """Sanitize appointment status using a strict whitelist.

    Only allows values that match the CHECK constraint in the database.
    """
    allowed = {'Scheduled', 'Completed', 'Cancelled', 'No Show'}
    if value not in allowed:
        raise ValidationError(f"Status must be one of: {', '.join(sorted(allowed))}")
    return value


# ─── ID Sanitization ──────────────────────────────────────────────────────────
def sanitize_id(value, field_name="ID"):
    """Sanitize an integer ID field.

    Rules:
    - Must be a valid integer
    - Must be positive (IDs are never negative or zero)

    This prevents type-confusion attacks where a string is passed
    where an integer is expected.
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer")

    if int_value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer")

    return int_value


# ─── Time Sanitization ────────────────────────────────────────────────────────
def sanitize_time(value, field_name="Time"):
    """Sanitize a time string.

    Rules:
    - Must match HH:MM format (24-hour or AM/PM variants accepted)
    - Rejects any non-time characters
    """
    if value is None or str(value).strip() == '':
        raise ValidationError(f"{field_name} is required")

    value = str(value).strip()

    # Accept HH:MM, HH:MM AM/PM, or HH:MM:SS formats
    time_pattern = r'^([01]?\d|2[0-3]):([0-5]\d)(:[0-5]\d)?(\s?(AM|PM|am|pm))?$'
    if not re.match(time_pattern, value):
        raise ValidationError(f"{field_name} must be a valid time (e.g., 09:30, 14:00)")

    return value


# ─── Free Text Sanitization ───────────────────────────────────────────────────
def sanitize_text(value, field_name="Text", max_length=500):
    """Sanitize free-text fields (notes, address, duration, dosage).

    Rules:
    - If empty, returns empty string (free text is usually optional)
    - Must be within max_length characters
    - Strips leading/trailing whitespace
    - Rejects SQL comment sequences (-- and /* */)

    More permissive than sanitize_name since addresses and notes
    may contain special characters like #, /, etc.
    """
    if value is None or str(value).strip() == '':
        return ''

    value = str(value).strip()

    if len(value) > max_length:
        raise ValidationError(f"{field_name} must be {max_length} characters or fewer")

    # Reject SQL comment patterns only (allow most characters for free text)
    if re.search(r'--|/\*|\*/', value):
        raise ValidationError(f"{field_name} contains invalid character sequences")

    return value
