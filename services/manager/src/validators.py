import re

from marshmallow import ValidationError


def phone_validator(value):
    MIN_LENGTH = 10
    MAX_LENGTH = 13
    if not re.match(f'\d{{{MIN_LENGTH},{MAX_LENGTH}}}', value):
        raise ValidationError(f"Phone number must be [{MIN_LENGTH}..{MAX_LENGTH}] digits")
    return value
